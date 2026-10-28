"""Phase two contracts: focused inspection primitives, not arbitrary command routing."""

import sys
from secripts.registry import Operation, Parameter


def additional():
    def command(name, title, summary, argv, **kw):
        return Operation(
            name, title, summary, name.split(".")[0], requires=(argv[0],), argv=tuple(argv), **kw
        )

    def inspect(name, title, summary, handler, **kw):
        return Operation(name, title, summary, name.split(".")[0], handler=handler, **kw)

    tree = (Parameter("tree", "Device-tree directory to audit", required=True, kind="path"),)
    image = (Parameter("artifact", "Image file to inspect", required=True, kind="path"),)
    device = (Parameter("device", "Optional explicit transport identifier; never persisted"),)
    return [
        command(
            "git.root",
            "Repository root",
            "Locate the current working-tree root.",
            ["git", "rev-parse", "--show-toplevel"],
        ),
        command(
            "git.branch",
            "Current branch",
            "Resolve branch name; detached HEAD is reported by Git.",
            ["git", "branch", "--show-current"],
        ),
        inspect(
            "git.health",
            "Repository health",
            "Combine root, branch, dirty state, upstream and local divergence.",
            "git_health",
            requires=("git",),
            tags=("repository", "divergence", "upstream"),
        ),
        command(
            "git.tags",
            "Recent tags",
            "List tags ordered by creation time without contacting remotes.",
            ["git", "tag", "--sort=-creatordate"],
        ),
        command(
            "git.worktrees",
            "Worktree inventory",
            "List existing worktrees and their branch relationships.",
            ["git", "worktree", "list", "--porcelain"],
        ),
        command(
            "git.submodules",
            "Submodule state",
            "Inspect recorded submodule revisions without initialization or update.",
            ["git", "submodule", "status"],
        ),
        command(
            "git.stashes",
            "Stash summary",
            "List stash references and subjects without showing patches.",
            ["git", "stash", "list", "--format=%gd %gs"],
        ),
        command(
            "git.ignored",
            "Ignored paths",
            "Inspect ignored untracked paths; file contents are never read.",
            ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
        ),
        command(
            "git.untracked",
            "Untracked paths",
            "Inspect untracked file names without reading their contents.",
            ["git", "ls-files", "--others", "--exclude-standard"],
        ),
        command(
            "git.changed",
            "Changed files",
            "Inspect tracked worktree changes without exposing patches.",
            ["git", "diff", "--name-status"],
        ),
        inspect(
            "git.largest",
            "Largest tracked working files",
            "Rank up to 10,000 tracked files by current disk size.",
            "git_largest",
            requires=("git",),
        ),
        command(
            "git.objects",
            "Object database size",
            "Inspect loose/packed Git object counts and storage.",
            ["git", "count-objects", "-vH"],
        ),
        command(
            "git.contributors",
            "Recent contributors",
            "Summarize authors of the most recent 200 commits.",
            ["git", "shortlog", "-sn", "HEAD", "-200"],
        ),
        command(
            "git.cleanup",
            "Branch review candidates",
            "List branches merged into HEAD; never delete branches.",
            ["git", "branch", "--merged", "HEAD"],
        ),
        inspect(
            "git.signatures",
            "Commit signature declarations",
            "Inspect signature-header presence without invoking a verifier.",
            "git_signatures",
            requires=("git",),
        ),
        command(
            "git.remote",
            "Remote reachability",
            "Explicitly contact origin and query its HEAD without fetching objects.",
            ["git", "ls-remote", "--exit-code", "origin", "HEAD"],
            network=True,
        ),
        command(
            "github.repository",
            "GitHub repository metadata",
            "Explicit network query for visibility, default branch, owner and viewer permissions.",
            [
                "gh",
                "repo",
                "view",
                "--json",
                "nameWithOwner,visibility,defaultBranchRef,viewerPermission,isArchived",
            ],
            network=True,
        ),
        command(
            "github.pulls",
            "Open pull requests",
            "Query the latest twenty open PR summaries.",
            ["gh", "pr", "list", "--limit", "20", "--json", "number,title,state,headRefName"],
            network=True,
        ),
        command(
            "github.workflows",
            "Workflow runs",
            "Query the latest ten workflow run states; do not infer billing causes.",
            [
                "gh",
                "run",
                "list",
                "--limit",
                "10",
                "--json",
                "databaseId,headSha,status,conclusion,workflowName",
            ],
            network=True,
        ),
        command(
            "github.releases",
            "Release summary",
            "Query the latest ten release summaries without downloading assets.",
            ["gh", "release", "list", "--limit", "10"],
            network=True,
        ),
        command(
            "github.issues",
            "Open issues",
            "Query the latest twenty issue summaries.",
            ["gh", "issue", "list", "--limit", "20", "--json", "number,title,state"],
            network=True,
        ),
        inspect(
            "python.environment",
            "Python environment",
            "Inspect interpreter, venv boundaries and developer-tool availability.",
            "python_environment",
        ),
        inspect(
            "python.project",
            "Python project metadata",
            "Parse allowlisted pyproject build metadata without executing backend code.",
            "python_project",
            tags=("build", "package", "pyproject"),
        ),
        inspect(
            "python.editables",
            "Editable installations",
            "Locate editable distributions using installed direct-url metadata.",
            "python_editables",
        ),
        command(
            "python.dependencies",
            "Dependency health",
            "Ask the current interpreter pip to validate installed dependency relationships.",
            [sys.executable, "-m", "pip", "check"],
        ),
        inspect(
            "java.environment",
            "JVM environment",
            "Inspect Java/Javac versions, JAVA_HOME, JDK paths and wrapper presence.",
            "java",
            tags=("jdk", "gradle", "maven"),
        ),
        inspect(
            "adb.inspect",
            "Android device dossier",
            "Collect allowlisted read-only identity, build, security and hardware observations.",
            "adb_inspect",
            requires=("adb",),
            parameters=device,
            device_required=True,
            tags=("device", "battery", "storage", "display"),
            effect="Read one explicitly selected or sole authorized ADB device. ADB may start its local daemon.",
        ),
        inspect(
            "fastboot.inspect",
            "Bootloader dossier",
            "Read selected safe Fastboot variables from one transport; no boot or flash.",
            "fastboot_inspect",
            requires=("fastboot",),
            parameters=device,
            device_required=True,
        ),
        inspect(
            "linux.environment",
            "Linux and PRoot context",
            "Inspect distro, architecture, build tools and host/guest boundary evidence.",
            "linux",
        ),
        command(
            "linux.packages",
            "Build package inventory",
            "Inspect installed versions of core development packages.",
            ["dpkg-query", "-W", "git", "make", "gcc", "python3", "pkg-config"],
        ),
        inspect(
            "network.configuration",
            "Local resolver configuration",
            "Inspect hostname and configured nameservers without resolving external hosts.",
            "network",
        ),
        command(
            "network.routes",
            "Local routing table",
            "Inspect local routes without transmitting probes.",
            ["ip", "route", "show"],
        ),
        command(
            "network.sockets",
            "Listening sockets",
            "Inspect local TCP/UDP listeners without probing other hosts.",
            ["ss", "-lntu"],
        ),
        inspect(
            "ssh.environment",
            "SSH environment",
            "Inspect client, agent socket and config-file presence; never read private keys.",
            "ssh",
        ),
        command(
            "ssh.agent",
            "Agent key fingerprints",
            "Ask the local agent for public-key fingerprints; no private key contents.",
            ["ssh-add", "-l"],
        ),
        command(
            "ssh.github",
            "GitHub SSH connectivity",
            "Explicit network authentication handshake; host-key policy is never bypassed.",
            [
                "ssh",
                "-T",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                "-o",
                "StrictHostKeyChecking=yes",
                "git@github.com",
            ],
            network=True,
            effect="Contacts GitHub using configured SSH identity. Successful GitHub authentication commonly exits 1; inspect the evidence.",
        ),
        inspect(
            "filesystem.capacity",
            "Filesystem evidence",
            "Inspect bytes, inode availability, temp access and current-directory permissions.",
            "filesystem",
        ),
        inspect(
            "environment.xdg",
            "XDG paths",
            "Inspect configured user-data/config/cache/state locations without creating them.",
            "xdg",
        ),
        inspect(
            "models.environment",
            "Local AI tooling",
            "Detect known executables and explicitly configured model directories only.",
            "models",
        ),
        inspect(
            "diagnostics.system",
            "System dossier",
            "Inspect distro, kernel, CPU count, memory and mount context.",
            "host_detail",
        ),
        inspect(
            "recovery.doctor",
            "Recovery build prerequisites",
            "Inspect tools, host suitability, workspace and unresolved dependencies.",
            "recovery_doctor",
            tags=("twrp", "build", "readiness"),
        ),
        inspect(
            "recovery.tree",
            "Recovery tree intelligence",
            "Audit static device-tree declarations and a bounded local dependency graph.",
            "recovery_tree",
            parameters=tree,
            tags=("device tree", "twrp", "fstab", "dependencies"),
        ),
        inspect(
            "recovery.image",
            "Recovery image structure",
            "Inspect image boundaries, ramdisk metadata and unverified AVB declarations.",
            "recovery_image",
            parameters=image,
            tags=("boot", "vendor_boot", "init_boot", "avb"),
        ),
    ]
