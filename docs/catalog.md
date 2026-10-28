# Operation catalog

Generated from `sec list --json`; update with `python tools/catalog.py`.

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
