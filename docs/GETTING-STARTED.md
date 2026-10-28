# Getting started

You need basic terminal knowledge, Python 3.11+ and a supported Linux/Termux environment.
Install from the checkout with `pipx install .`; run `pipx ensurepath` if its bin directory
is absent from PATH. Development installation is described in [Development](DEVELOPMENT.md).

```sh
js --version
js help
js guide
js doc --json
js dos --json
js fd android
js sh android.sdk.validate
js exp android.sdk.validate
js run android.sdk.validate --dry-run
```

`js` opens guided entry only when both input and output are terminals. In scripts it
prints help and exits successfully. `js guide` offers orientation in either environment.
Nothing is automatically installed. A missing SDK/tool is evidence, not an invitation
to accept licenses or alter the host silently. Diagnostics can contain WARN/UNKNOWN.

A **command** selects functionality; an **operation ID** identifies a typed guarded task;
a **recipe** composes those tasks. Start with `js rcps`, inspect a recipe using `js rcp sh
NAME`, then use its dry-run before execution. Uppercase operands in manuals are placeholders.

[CLI guide](CLI-GUIDE.md) explains the interface. For a phone project, follow
[Build a Recovery](BUILD-A-RECOVERY.md). For experts, read the [contracts](architecture.md).
