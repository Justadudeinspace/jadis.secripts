# Operation catalog

Generated from `js ls --json`; update with `python tools/catalog.py`.

| Operation | Summary | Risk |
|---|---|---|
| `git.status` | Show branch and working tree changes. | READ_ONLY |
| `git.branches` | Inspect local branch names and upstream tracking. | READ_ONLY |
| `git.remotes` | Inspect remote URLs; credentials are redacted. | READ_ONLY |
| `git.log` | Show the latest twelve commits without diffs. | READ_ONLY |
| `git.integrity` | Check reachable object connectivity without repair. | READ_ONLY |
| `github.auth` | Ask gh for authentication status, never tokens. | READ_ONLY |
| `adb.devices` | List ADB transports. A listed device is not recovery qualification. | READ_ONLY |
| `adb.version` | Inspect the installed Android Debug Bridge version. | READ_ONLY |
| `fastboot.devices` | Enumerate bootloader transports without modifying devices. | READ_ONLY |
| `fastboot.version` | Inspect the installed Fastboot client version. | READ_ONLY |
| `android.sdk.validate` | Inspect configured SDK paths and installed components; never accept licenses automatically. | READ_ONLY |
| `environment.path` | Find absent, repeated and writable PATH entries. | READ_ONLY |
| `environment.runtimes` | Inspect developer tools and report missing prerequisites honestly. | READ_ONLY |
| `termux.inspect` | Inspect Termux and PRoot indicators without assuming Android host access. | READ_ONLY |
| `debian.packages` | Query installed build packages without installing or upgrading anything. | READ_ONLY |
| `ssh.version` | Inspect OpenSSH without reading private keys or contacting hosts. | READ_ONLY |
| `models.ollama` | Inspect Ollama version; no model downloads or provider credentials. | READ_ONLY |
| `network.interfaces` | Inspect local interface addresses; no external requests. | READ_ONLY |
| `repo.disk` | Show free space for the current filesystem. | READ_ONLY |
| `diagnostics.host` | Inspect OS, architecture and Python with explicit unknown states. | READ_ONLY |
| `git.root` | Locate the current working-tree root. | READ_ONLY |
| `git.branch` | Resolve branch name; detached HEAD is reported by Git. | READ_ONLY |
| `git.health` | Combine root, branch, dirty state, upstream and local divergence. | READ_ONLY |
| `git.tags` | List tags ordered by creation time without contacting remotes. | READ_ONLY |
| `git.worktrees` | List existing worktrees and their branch relationships. | READ_ONLY |
| `git.submodules` | Inspect recorded submodule revisions without initialization or update. | READ_ONLY |
| `git.stashes` | List stash references and subjects without showing patches. | READ_ONLY |
| `git.ignored` | Inspect ignored untracked paths; file contents are never read. | READ_ONLY |
| `git.untracked` | Inspect untracked file names without reading their contents. | READ_ONLY |
| `git.changed` | Inspect tracked worktree changes without exposing patches. | READ_ONLY |
| `git.largest` | Rank up to 10,000 tracked files by current disk size. | READ_ONLY |
| `git.objects` | Inspect loose/packed Git object counts and storage. | READ_ONLY |
| `git.contributors` | Summarize authors of the most recent 200 commits. | READ_ONLY |
| `git.cleanup` | List branches merged into HEAD; never delete branches. | READ_ONLY |
| `git.signatures` | Inspect signature-header presence without invoking a verifier. | READ_ONLY |
| `git.remote` | Explicitly contact origin and query its HEAD without fetching objects. | READ_ONLY |
| `github.repository` | Explicit network query for visibility, default branch, owner and viewer permissions. | READ_ONLY |
| `github.pulls` | Query the latest twenty open PR summaries. | READ_ONLY |
| `github.workflows` | Query the latest ten workflow run states; do not infer billing causes. | READ_ONLY |
| `github.releases` | Query the latest ten release summaries without downloading assets. | READ_ONLY |
| `github.issues` | Query the latest twenty issue summaries. | READ_ONLY |
| `python.environment` | Inspect interpreter, venv boundaries and developer-tool availability. | READ_ONLY |
| `python.project` | Parse allowlisted pyproject build metadata without executing backend code. | READ_ONLY |
| `python.editables` | Locate editable distributions using installed direct-url metadata. | READ_ONLY |
| `python.dependencies` | Ask the current interpreter pip to validate installed dependency relationships. | READ_ONLY |
| `java.environment` | Inspect Java/Javac versions, JAVA_HOME, JDK paths and wrapper presence. | READ_ONLY |
| `adb.inspect` | Collect allowlisted read-only identity, build, security and hardware observations. | READ_ONLY |
| `fastboot.inspect` | Read selected safe Fastboot variables from one transport; no boot or flash. | READ_ONLY |
| `linux.environment` | Inspect distro, architecture, build tools and host/guest boundary evidence. | READ_ONLY |
| `linux.packages` | Inspect installed versions of core development packages. | READ_ONLY |
| `network.configuration` | Inspect hostname and configured nameservers without resolving external hosts. | READ_ONLY |
| `network.routes` | Inspect local routes without transmitting probes. | READ_ONLY |
| `network.sockets` | Inspect local TCP/UDP listeners without probing other hosts. | READ_ONLY |
| `ssh.environment` | Inspect client, agent socket and config-file presence; never read private keys. | READ_ONLY |
| `ssh.agent` | Ask the local agent for public-key fingerprints; no private key contents. | READ_ONLY |
| `ssh.github` | Explicit network authentication handshake; host-key policy is never bypassed. | READ_ONLY |
| `filesystem.capacity` | Inspect bytes, inode availability, temp access and current-directory permissions. | READ_ONLY |
| `environment.xdg` | Inspect configured user-data/config/cache/state locations without creating them. | READ_ONLY |
| `models.environment` | Detect known executables and explicitly configured model directories only. | READ_ONLY |
| `diagnostics.system` | Inspect distro, kernel, CPU count, memory and mount context. | READ_ONLY |
| `recovery.doctor` | Inspect tools, host suitability, workspace and unresolved dependencies. | READ_ONLY |
| `recovery.tree` | Audit static device-tree declarations and a bounded local dependency graph. | READ_ONLY |
| `recovery.image` | Inspect image boundaries, ramdisk metadata and unverified AVB declarations. | READ_ONLY |
| `image.inspect` | Identify and inspect bounded image structures without executing payloads. | READ_ONLY |
| `image.providers` | Inspect optional installed tooling and native formats without invoking providers. | READ_ONLY |
| `recovery.model` | Inspect source-linked facts, conflicts and unresolved device evidence. | READ_ONLY |
| `recovery.diagnose` | Explain generation hints, dependencies and reasons a tree needs review. | READ_ONLY |
| `recovery.plan` | Correlate device/source/tree/host evidence; never sync, build or qualify hardware. | READ_ONLY |
| `recovery.host` | Inspect architecture, memory, disk, prerequisites and unqualified boundaries. | READ_ONLY |
| `recovery.derive` | Generate a new candidate tree with per-line evidence; never overwrite or claim build readiness. | MUTATING |
| `image.differential` | Explicit hash-pinned AOSP unpack/repack comparison; no corpus tools. | READ_ONLY |
| `image.model` | Inspect complete supported artifact structure without payload dumps. | READ_ONLY |
| `image.unpack` | Create a new isolated artifact workspace, preserving source and section hashes. | MUTATING |
| `image.workspace` | Inspect versioned model and immutable source hash. | READ_ONLY |
| `image.rebuild` | Reconstruct a new artifact from an explicit workspace; never overwrite source. | MUTATING |
| `image.compare` | Compare bytes, structure, components, metadata and semantic evidence independently. | READ_ONLY |
| `image.roundtrip` | Extract, reconstruct, reparse and compare; device qualification remains UNTESTED. | MUTATING |
| `ramdisk.inspect` | Decode bounded streams and model newc/CRC entries without extraction. | READ_ONLY |
| `ramdisk.extract` | Create numbered payload files and metadata; never materialize archive symlinks or special files. | MUTATING |
| `ramdisk.pack` | Pack a virtual workspace or safe directory deterministically into a new artifact. | MUTATING |
| `ramdisk.compare` | Explain file, mode, owner, link, order and encoding differences. | READ_ONLY |
| `dtbo.inspect` | Inspect entry metadata, shared blobs and supported FDT structures. | READ_ONLY |
| `dtbo.extract` | Create an isolated workspace with individually bounded DT blobs. | MUTATING |
| `dtbo.rebuild` | Create a canonical DT table with shared identical blobs and validated entries. | MUTATING |
| `dtbo.compare` | Separate table layout from entry metadata and blob content. | READ_ONLY |
| `avb.inspect` | Inspect authentication, auxiliary regions, descriptor types and public-key identity. | READ_ONLY |
| `avb.verify` | Explicit optional avbtool signature/key verification plus native descriptor hash checks; no device trust claim. | READ_ONLY |
