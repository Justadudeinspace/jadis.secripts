"""One typed contract drives execution, discovery, documentation and menus."""

from dataclasses import asdict, dataclass
import re
from secripts.safety import Risk, SecError


@dataclass(frozen=True)
class Operation:
    id: str
    title: str
    summary: str
    category: str
    risk: Risk = Risk.READ_ONLY
    requires: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ("linux", "termux")
    network: bool = False
    device_required: bool = False
    receipt: bool = True
    effect: str = "Inspect local state; no intended configuration changes."
    output: str = "Diagnostic evidence"
    handler: str = "command"
    argv: tuple[str, ...] = ()
    legacy: tuple[str, ...] = ()

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)+", self.id):
            raise ValueError("Invalid operation ID")
        if not all((self.title.strip(), self.summary.strip(), self.category.strip(), self.effect)):
            raise ValueError("Descriptions and category are required")
        if not isinstance(self.risk, Risk):
            raise ValueError("Invalid risk class")
        if self.handler == "command" and not self.argv:
            raise ValueError("Command operation needs argv")

    def metadata(self) -> dict:
        return asdict(self)


class Registry:
    def __init__(self, operations):
        self.operations = {}
        for op in operations:
            if op.id in self.operations:
                raise ValueError(f"Duplicate operation: {op.id}")
            self.operations[op.id] = op

    def get(self, name: str) -> Operation:
        try:
            return self.operations[name]
        except KeyError as exc:
            raise SecError(f"Unknown operation: {name}. Use sec find <query>.", 2) from exc

    def search(self, query: str = "") -> list[Operation]:
        words = query.casefold().split()
        return [
            op
            for op in self.operations.values()
            if all(w in str(op.metadata()).casefold() for w in words)
        ]


def registry() -> Registry:
    def cmd(name, title, summary, category, argv, legacy=(), **kwargs):
        return Operation(
            name,
            title,
            summary,
            category,
            argv=tuple(argv),
            requires=(argv[0],),
            legacy=legacy,
            **kwargs,
        )

    return Registry(
        [
            cmd(
                "git.status",
                "Repository status",
                "Show branch and working tree changes.",
                "git",
                ["git", "--no-optional-locks", "status", "--short", "--branch"],
                ("legacy-0136",),
            ),
            cmd(
                "git.branches",
                "Local branches",
                "Inspect local branch names and upstream tracking.",
                "git",
                ["git", "branch", "-vv"],
                ("legacy-0136",),
            ),
            cmd(
                "git.remotes",
                "Repository remotes",
                "Inspect remote URLs; credentials are redacted.",
                "git",
                ["git", "remote", "-v"],
                ("legacy-0122",),
            ),
            cmd(
                "git.log",
                "Recent history",
                "Show the latest twelve commits without diffs.",
                "git",
                ["git", "log", "-12", "--oneline"],
                ("legacy-0136",),
            ),
            cmd(
                "git.integrity",
                "Repository integrity",
                "Check reachable object connectivity without repair.",
                "git",
                ["git", "fsck", "--connectivity-only", "--no-reflogs"],
                ("legacy-0136",),
            ),
            cmd(
                "github.auth",
                "GitHub authentication status",
                "Ask gh for authentication status, never tokens.",
                "github",
                ["gh", "auth", "status"],
                network=True,
            ),
            cmd(
                "adb.devices",
                "ADB devices",
                "List ADB transports. A listed device is not recovery qualification.",
                "adb",
                ["adb", "devices", "-l"],
                ("legacy-0000",),
                effect="ADB may start its local daemon; no device configuration is changed.",
            ),
            cmd(
                "adb.version",
                "ADB version",
                "Inspect the installed Android Debug Bridge version.",
                "adb",
                ["adb", "version"],
                ("legacy-0009",),
            ),
            cmd(
                "fastboot.devices",
                "Fastboot devices",
                "Enumerate bootloader transports without modifying devices.",
                "fastboot",
                ["fastboot", "devices", "-l"],
                ("legacy-0032",),
            ),
            cmd(
                "fastboot.version",
                "Fastboot version",
                "Inspect the installed Fastboot client version.",
                "fastboot",
                ["fastboot", "--version"],
                ("legacy-0032",),
            ),
            Operation(
                "android.sdk.validate",
                "Validate Android SDK",
                "Inspect configured SDK paths and installed components; never accept licenses automatically.",
                "android",
                handler="sdk",
                tags=("sdk", "license", "platform tools"),
                legacy=("legacy-0003", "legacy-0013"),
            ),
            Operation(
                "environment.path",
                "Analyze PATH",
                "Find absent, repeated and writable PATH entries.",
                "environment",
                handler="path",
            ),
            Operation(
                "environment.runtimes",
                "Runtime health",
                "Inspect developer tools and report missing prerequisites honestly.",
                "environment",
                handler="doctor",
                legacy=("legacy-0024",),
            ),
            Operation(
                "termux.inspect",
                "Termux boundaries",
                "Inspect Termux and PRoot indicators without assuming Android host access.",
                "termux",
                handler="host",
                legacy=("legacy-0024",),
            ),
            Operation(
                "debian.packages",
                "Debian development packages",
                "Query installed build packages without installing or upgrading anything.",
                "debian",
                requires=("dpkg-query",),
                argv=("dpkg-query", "-W", "git", "build-essential", "python3", "openjdk-17-jdk"),
                legacy=("legacy-0024",),
            ),
            cmd(
                "ssh.version",
                "SSH client version",
                "Inspect OpenSSH without reading private keys or contacting hosts.",
                "ssh",
                ["ssh", "-V"],
            ),
            cmd(
                "models.ollama",
                "Local model runtime",
                "Inspect Ollama version; no model downloads or provider credentials.",
                "models",
                ["ollama", "--version"],
            ),
            cmd(
                "network.interfaces",
                "Network interfaces",
                "Inspect local interface addresses; no external requests.",
                "network",
                ["ip", "-brief", "address"],
            ),
            cmd(
                "repo.disk",
                "Filesystem capacity",
                "Show free space for the current filesystem.",
                "repo",
                ["df", "-h", "."],
            ),
            Operation(
                "diagnostics.host",
                "Host context",
                "Inspect OS, architecture and Python with explicit unknown states.",
                "diagnostics",
                handler="host",
            ),
        ]
    )
