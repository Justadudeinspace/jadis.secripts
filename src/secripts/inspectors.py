"""Bounded local developer inspections. No automatic install, network probe or model search."""

import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import sys
import tempfile
from secripts.context import host
from secripts.evidence import observation, overall


def read_text(path, limit=128 * 1024):
    try:
        with Path(path).open() as stream:
            return stream.read(limit)
    except (OSError, UnicodeError):
        return None


def tools(names):
    return {
        name: observation(
            "PASS" if shutil.which(name) else "WARN",
            shutil.which(name),
            "Executable presence only; functionality is not qualified",
            f"Inspect/install {name} only if required by your workflow",
        )
        for name in names
    }


def host_detail(c=None, **params):
    release = platform.freedesktop_os_release() if Path("/etc/os-release").exists() else {}
    memory = read_text("/proc/meminfo")
    return {
        **host(),
        "kernel": platform.release(),
        "distribution": release,
        "cpu_count": os.cpu_count(),
        "memory": memory or "UNKNOWN",
        "shell": os.environ.get("SHELL", "UNKNOWN"),
        "hostname": socket.gethostname(),
        "mounts": read_text("/proc/mounts") or "UNKNOWN",
        "status": "PASS",
    }


def filesystem(c=None, **params):
    current = Path.cwd()
    disk = shutil.disk_usage(current)
    values = {
        "cwd": str(current),
        "free_bytes": disk.free,
        "total_bytes": disk.total,
        "temp": tempfile.gettempdir(),
        "temp_writable": os.access(tempfile.gettempdir(), os.W_OK),
        "cwd_writable": os.access(current, os.W_OK),
        "status": "PASS",
    }
    try:
        stat = os.statvfs(current)
        values.update(inodes_free=stat.f_favail, inodes_total=stat.f_files, mount_flags=stat.f_flag)
    except OSError:
        values["inodes"] = "UNKNOWN"
    if not values["temp_writable"] or not disk.free:
        values["status"] = "WARN"
    return values


def python_environment(c=None, **params):
    return {
        "status": "PASS",
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "virtual_environment": sys.prefix != sys.base_prefix,
        "virtual_env_variable": os.environ.get("VIRTUAL_ENV"),
        "prefix_conflict": bool(
            os.environ.get("VIRTUAL_ENV")
            and Path(os.environ["VIRTUAL_ENV"]).resolve() != Path(sys.prefix).resolve()
        ),
        "modules": {
            name: bool(importlib.util.find_spec(name))
            for name in ("pip", "pytest", "ruff", "build")
        },
        "tools": tools(("python", "python3", "pip", "pipx", "pytest", "ruff")),
    }


def python_project(c=None, **params):
    import tomllib

    path = Path.cwd() / "pyproject.toml"
    if not path.is_file():
        return {"status": "UNKNOWN", "reason": "No pyproject.toml in current directory"}
    try:
        if path.stat().st_size > 1024 * 1024:
            return {"status": "WARN", "reason": "Project metadata exceeds 1 MiB inspection limit"}
        value = tomllib.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return {"status": "FAIL", "reason": f"Invalid project metadata: {exc}"}
    project, build = value.get("project", {}), value.get("build-system", {})
    # Deliberate allowlist: arbitrary tool tables can contain credentials.
    return {
        "status": "PASS" if build.get("build-backend") else "WARN",
        "path": str(path),
        "project": {k: project.get(k) for k in ("name", "version", "requires-python", "dynamic")},
        "build_backend": build.get("build-backend"),
        "build_requirements": build.get("requires", []),
        "dependency_count": len(project.get("dependencies", [])),
        "note": "Metadata inspection does not build or install dependencies",
    }


def python_editables(c=None, **params):
    projects = []
    for distribution in importlib.metadata.distributions():
        text = distribution.read_text("direct_url.json")
        if text:
            try:
                info = json.loads(text)
            except ValueError:
                continue
            if info.get("dir_info", {}).get("editable"):
                projects.append(
                    {
                        "name": distribution.metadata.get("Name"),
                        "version": distribution.version,
                        "source": info.get("url"),
                    }
                )
    return {"status": "PASS", "projects": sorted(projects, key=lambda p: p["name"] or "")}


def java(c, **params):
    results = tools(("java", "javac", "gradle", "mvn"))
    for name, args in (
        ("java", ["java", "-XshowSettings:properties", "-version"]),
        ("javac", ["javac", "-version"]),
    ):
        if shutil.which(name):
            result = c.command(args)
            output = result.get("stdout", "") + "\n" + result.get("stderr", "")
            # Only version/architecture/home properties; never arbitrary JVM properties.
            lines = [
                line.strip()
                for line in output.splitlines()
                if any(
                    key in line
                    for key in ("java.version =", "java.home =", "os.arch =", 'version "', "javac ")
                )
            ]
            results[name] = observation("PASS" if result["result"] == "PASS" else "WARN", lines)
            result["stdout"], result["stderr"] = "\n".join(lines), ""
    root = Path("/usr/lib/jvm")
    jdks = sorted(p.name for p in root.iterdir())[:40] if root.is_dir() else []
    return {
        "status": overall(results.values()),
        "tools": results,
        "java_home": os.environ.get("JAVA_HOME"),
        "available_jdks": jdks,
        "gradle_wrapper": (Path.cwd() / "gradlew").is_file(),
        "android_jdk_compatibility": "UNKNOWN: branch-specific; executable/version is not build qualification",
    }


def sdk(c=None, **params):
    roots = {k: os.environ.get(k) for k in ("ANDROID_HOME", "ANDROID_SDK_ROOT")}
    root = roots["ANDROID_HOME"] or roots["ANDROID_SDK_ROOT"]
    conflict = bool(
        all(roots.values())
        and Path(roots["ANDROID_HOME"]).resolve() != Path(roots["ANDROID_SDK_ROOT"]).resolve()
    )
    groups = {}
    for name in (
        "platform-tools",
        "build-tools",
        "platforms",
        "cmdline-tools",
        "emulator",
        "ndk",
        "cmake",
        "licenses",
    ):
        path = Path(root) / name if root else None
        present = bool(path and path.is_dir())
        versions = (
            sorted(p.name for p in path.iterdir())[:100]
            if present and name not in ("platform-tools", "emulator", "licenses")
            else []
        )
        groups[name] = {"status": "PASS" if present else "WARN", "entries": versions}
    candidates = []
    if root:
        for tool in ("sdkmanager", "avdmanager"):
            candidates.extend(
                str(p) for p in (Path(root) / "cmdline-tools").glob(f"*/bin/{tool}") if p.is_file()
            )
    status = (
        "WARN"
        if conflict
        or not root
        or not Path(root).is_dir()
        or any(
            groups[n]["status"] != "PASS" for n in ("platform-tools", "platforms", "build-tools")
        )
        else "PASS"
    )
    return {
        "status": status,
        "roots": roots,
        "selected_root": root,
        "conflict": conflict,
        "components": groups,
        "manager_paths": sorted(candidates),
        "canonical_roots": sorted({str(Path(p).resolve()) for p in roots.values() if p}),
        "license_state": "UNKNOWN: directory/file presence does not prove acceptance",
        "compatibility": "UNTESTED: installed version lists do not establish project compatibility",
        "remediation": "Choose one canonical SDK root; inspect missing components manually. No licenses accepted.",
    }


def termux(c=None, **params):
    value = host()
    prefix = os.environ.get("PREFIX")
    return {
        "status": "PASS" if value["termux"] else "UNSUPPORTED",
        "host": value,
        "prefix": prefix,
        "android_api_context": os.environ.get("ANDROID_ROOT") or "UNKNOWN",
        "storage_links_present": (Path.home() / "storage/shared").exists(),
        "tools": tools(
            (
                "pkg",
                "apt",
                "dpkg-query",
                "termux-info",
                "termux-battery-status",
                "proot",
                "proot-distro",
            )
        ),
        "wake_lock": "UNKNOWN: no safe state probe available",
        "boundary": "Runtime origin is detectable; Android host/guest ownership and permissions are not inferred",
    }


def linux(c=None, **params):
    return {
        "status": "PASS" if platform.system() in ("Linux", "Android") else "UNSUPPORTED",
        "host": host(),
        "distribution": read_text("/etc/os-release") or "UNKNOWN",
        "architecture": platform.machine(),
        "tools": tools(("apt", "dpkg-query", "make", "gcc", "git", "python3", "java", "proot")),
        "memory": read_text("/proc/meminfo") or "UNKNOWN",
        "boundary": "PRoot indicators are hints; absence does not establish a native host",
    }


def network(c=None, **params):
    # Local resolver configuration only. No DNS lookup or connection is performed.
    text = read_text("/etc/resolv.conf")
    nameservers = [
        line.split()[1]
        for line in (text or "").splitlines()
        if line.startswith("nameserver ") and len(line.split()) > 1
    ]
    return {
        "status": "PASS" if text is not None else "UNKNOWN",
        "hostname": socket.gethostname(),
        "nameservers": nameservers,
        "tools": tools(("ip", "ss", "getent")),
        "connectivity": "UNTESTED: no external requests",
    }


def ssh(c=None, **params):
    root = Path.home() / ".ssh"
    return {
        "status": "PASS" if shutil.which("ssh") else "WARN",
        "tools": tools(("ssh", "ssh-add")),
        "agent_socket_present": bool(
            os.environ.get("SSH_AUTH_SOCK") and Path(os.environ["SSH_AUTH_SOCK"]).exists()
        ),
        "config_present": (root / "config").is_file(),
        "known_hosts_present": (root / "known_hosts").is_file(),
        "private_keys": "NOT_READ",
        "loaded_keys": "UNTESTED: run ssh.agent explicitly",
    }


def models(c=None, **params):
    configured = {k: os.environ[k] for k in ("OLLAMA_MODELS", "LLAMA_CACHE") if os.environ.get(k)}
    return {
        "status": "PASS",
        "tools": tools(
            (
                "ollama",
                "llama-cli",
                "llama-server",
                "llama-cpp",
                "claude",
                "gemini",
                "codex",
                "aider",
            )
        ),
        "configured_directories": {
            k: {"path": v, "exists": Path(v).is_dir()} for k, v in configured.items()
        },
        "provider_configuration": "NOT_READ",
        "models": "NOT_ENUMERATED: configured directories only",
    }


def xdg(c=None, **params):
    defaults = {
        "XDG_CONFIG_HOME": Path.home() / ".config",
        "XDG_DATA_HOME": Path.home() / ".local/share",
        "XDG_CACHE_HOME": Path.home() / ".cache",
        "XDG_STATE_HOME": Path.home() / ".local/state",
    }
    return {
        "status": "PASS",
        "paths": {k: str(Path(os.environ.get(k, v))) for k, v in defaults.items()},
        "secripts_override": os.environ.get("SECRIPTS_DATA_HOME"),
    }


def git_health(c, **params):
    root = c.text(["git", "rev-parse", "--show-toplevel"])
    if not root:
        return {"status": "UNKNOWN", "reason": "Not a Git worktree or Git failed"}
    branch = c.text(["git", "symbolic-ref", "--quiet", "--short", "HEAD"])
    dirty = c.text(
        ["git", "-c", "core.fsmonitor=false", "--no-optional-locks", "status", "--porcelain"]
    )
    upstream = c.text(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"])
    divergence = (
        c.text(["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"])
        if upstream
        else None
    )
    return {
        "status": "WARN" if dirty is None or not branch or not upstream else "PASS",
        "root": root,
        "branch": branch or "DETACHED/UNRESOLVED",
        "dirty": None if dirty is None else bool(dirty),
        "upstream": upstream or "UNKNOWN",
        "divergence": divergence or "UNKNOWN",
        "remote_reachability": "UNTESTED: local refs only",
    }


def git_largest(c, **params):
    output = c.text(["git", "ls-files", "-z"])
    if output is None:
        return {"status": "FAIL", "reason": "Cannot enumerate tracked files"}
    values = []
    for name in output.split("\0")[:10000]:
        path = Path(name)
        if name and not path.is_symlink() and path.is_file():
            values.append({"path": name, "bytes": path.stat().st_size})
    return {
        "status": "WARN" if "[TRUNCATED]" in output else "PASS",
        "files": sorted(values, key=lambda v: (-v["bytes"], v["path"]))[:20],
        "limit": "First 10,000 tracked paths; working-file sizes, not Git blob sizes",
    }


def recovery_doctor(c=None, **params):
    from secripts.recovery.workspace import recovery_doctor as inspect

    return inspect()


def recovery_tree(c=None, **params):
    from secripts.recovery.inspection import audit_tree

    return audit_tree(Path(params["tree"]))


def recovery_image(c=None, **params):
    from secripts.recovery.inspection import inspect_image

    return inspect_image(Path(params["artifact"]))


HANDLERS = {
    "host_detail": host_detail,
    "filesystem": filesystem,
    "python_environment": python_environment,
    "python_project": python_project,
    "python_editables": python_editables,
    "java": java,
    "sdk": sdk,
    "termux": termux,
    "linux": linux,
    "network": network,
    "ssh": ssh,
    "models": models,
    "xdg": xdg,
    "git_health": git_health,
    "git_largest": git_largest,
    "recovery_doctor": recovery_doctor,
    "recovery_tree": recovery_tree,
    "recovery_image": recovery_image,
}


def git_signatures(c, **params):
    value = c.command(["git", "cat-file", "-p", "HEAD"])
    headers = value.get("stdout", "").split("\n\n", 1)[0]
    signed = any(line.startswith(("gpgsig ", "gpgsig-sha256 ")) for line in headers.splitlines())
    value["stdout"] = "Commit payload omitted; signature-header presence inspected"
    return {
        "status": "PASS" if value["result"] == "PASS" else "UNKNOWN",
        "signature_header_present": signed if value["result"] == "PASS" else None,
        "cryptographic_verification": "UNTESTED: no verifier invoked",
    }


HANDLERS["git_signatures"] = git_signatures
