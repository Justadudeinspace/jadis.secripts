"""Approachable entry and topic orientation; every action routes to the canonical CLI."""

import sys

TOPICS = {
    "image": (
        "Image Laboratory",
        "Identify, model, unpack, rebuild and compare offline artifacts. Reconstruction is not bootability.",
        ["js insp IMAGE --json", "js img --help", "js img rt IMAGE --json"],
        "docs/IMAGE-LAB.md",
    ),
    "recovery": (
        "Recovery Laboratory",
        "Start with evidence acquisition, then model, tree review and a build plan. No device mutation.",
        [
            "js ry acquire",
            "js ry status MODEL --json",
            "js ry flags MODEL --json",
            "js ry plan MODEL --json",
        ],
        "docs/BUILD-A-RECOVERY.md",
    ),
    "device": (
        "Device intelligence",
        "Explicit authorized read-only transport inspection. No root or hardware qualification.",
        ["js dce transports --json", "js dce insp --device TRANSPORT --json"],
        "docs/DEVICE-MODELS.md",
    ),
    "evidence": (
        "Evidence and receipts",
        "Operation identity is independent of CLI spelling. Invocation success does not upgrade diagnostic states.",
        ["js hist --summary --limit 10", "js rcpt latest --json"],
        "docs/RECEIPTS-EVIDENCE.md",
    ),
    "ai": (
        "AI advice",
        "Preview redacted context locally; approve its hash before any external inference. AI has no execution tools.",
        ["js ai setup", "js ai context --help", "js ai ask --help"],
        "docs/AI.md",
    ),
}


def topic(name=None):
    if name is None:
        return {
            "title": "JADIS // SECRIPTS",
            "topics": {k: v[1] for k, v in TOPICS.items()},
            "start": ["js guide", "js 1337", "js doc", "js dos", "js fd"],
            "manual": "docs/GETTING-STARTED.md",
        }
    from secripts.safety import SecError

    if name not in TOPICS:
        raise SecError("Unknown help topic; use image, recovery, device, evidence or ai", 2)
    title, purpose, commands, manual = TOPICS[name]
    return {"title": title, "purpose": purpose, "examples": commands, "manual": manual}


def guide(emit):
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        emit(topic())
        return 0
    choices = [
        (
            "Developer tools & diagnostics",
            "Inspect host health and discover typed operations.",
            ["dos"],
        ),
        (
            "Android device inspection",
            "Learn explicit read-only transport selection.",
            ["help", "device"],
        ),
        (
            "Analyze an Android image",
            "Learn inspection and reconstruction without device actions.",
            ["help", "image"],
        ),
        (
            "Work with a ramdisk",
            "Inspect/extract/pack virtual CPIO workspaces safely.",
            ["ram", "--help"],
        ),
        (
            "Recovery engineering",
            "Choose available evidence and understand the next steps.",
            ["ry", "acquire"],
        ),
        (
            "Guided workflows",
            "List recipes built from the same guarded operation contracts.",
            ["rcps"],
        ),
        (
            "Evidence & history",
            "Understand receipts, failures and unresolved qualification.",
            ["help", "evidence"],
        ),
        (
            "System doctor",
            "Read diagnostic states without installing or changing anything.",
            ["doc"],
        ),
        ("Advanced cockpit", "Open the JADIS operator console.", ["1337"]),
        (
            "AI assistant",
            "Inspect configuration and privacy before any network call.",
            ["ai", "setup"],
        ),
    ]
    from secripts.cli import main

    while True:
        print("JADIS // SECRIPTS\nWhat do you want to do?")
        for n, (title, description, _) in enumerate(choices, 1):
            print(f"[{n}] {title}\n    {description}")
        try:
            choice = input("Number, H for help, Q to exit > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return 0
        if choice in {"q", "quit", "exit"}:
            return 0
        if choice == "h":
            emit(topic())
            continue
        if choice.isdecimal() and 1 <= int(choice) <= len(choices):
            try:
                main(choices[int(choice) - 1][2])
            except SystemExit as exc:
                if exc.code:
                    emit({"error": "Use the displayed command help", "exit_code": exc.code})
        else:
            print("Choose a displayed number, H or Q.")
