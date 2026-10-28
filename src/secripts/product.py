"""Product-level evidence operations using the existing registry and dispatcher."""


def operations():
    from secripts.registry import Operation, Parameter

    definitions = [
        (
            "recovery.acquire",
            "Plan recovery evidence acquisition",
            "Explain required artifacts and inspect explicitly supplied local evidence; never download, extract or modify a device.",
            ("have", "artifact", "tree", "model"),
            (),
        ),
        (
            "recovery.build.diagnose",
            "Diagnose bounded build failure",
            "Classify observed log symptoms conservatively and correlate optional static tree context; root cause remains unresolved.",
            ("artifact", "tree"),
            ("artifact",),
        ),
        (
            "recovery.source",
            "Recovery source intelligence",
            "Inspect configured manifest/toolchain declarations and research-backed source options without synchronizing sources.",
            ("workspace",),
            (),
        ),
        (
            "ai.context",
            "Preview AI context",
            "Inspect exactly the bounded redacted JSON payload that can be approved for external transmission; no network.",
            ("artifact",),
            (),
        ),
        (
            "ai.providers",
            "AI provider configuration",
            "Show provider-specific environment indirection and authentication boundaries without exposing credentials or calling APIs.",
            (),
            (),
        ),
    ]
    definitions.extend(
        [
            (
                "recovery.architecture",
                "Composite recovery architecture",
                "Inspect independent artifact/resource relationships and the evidence-backed multi-output graph.",
                ("model",),
                ("model",),
            ),
            (
                "recovery.flags",
                "Inspect typed recovery configuration",
                "Inspect observed, derived, default and USER_OVERRIDE layers without changing evidence.",
                ("model",),
                ("model",),
            ),
            (
                "recovery.flags.validate",
                "Validate recovery configuration",
                "Detect known flag conflicts, unsupported generations and unresolved dependencies.",
                ("model",),
                ("model",),
            ),
            (
                "recovery.dependencies",
                "Inspect pinned recovery dependencies",
                "Validate selected dependency commits and checkout cleanliness; no acquisition.",
                ("model",),
                ("model",),
            ),
            (
                "recovery.status",
                "Persistent recovery project status",
                "Summarize current evidence and stale build inputs with a deterministic next action.",
                ("model",),
                ("model",),
            ),
            (
                "recovery.fstab",
                "Review structured fstab evidence",
                "Correlate safe mount declarations and conflicts without guessing block-device paths.",
                ("model",),
                ("model",),
            ),
        ]
    )
    return [
        Operation(
            id,
            title,
            summary,
            id.split(".")[0],
            handler="product",
            receipt=id != "ai.context",
            parameters=tuple(
                Parameter(
                    p,
                    "Explicit " + p + " evidence selector",
                    p in required,
                    "text" if p in {"have", "model"} else "path",
                )
                for p in params
            ),
        )
        for id, title, summary, params, required in definitions
    ]


def handle(id, p):
    if id in {
        "recovery.architecture",
        "recovery.flags",
        "recovery.flags.validate",
        "recovery.dependencies",
        "recovery.status",
        "recovery.fstab",
    }:
        from secripts.recovery import model, architecture, flags, dependencies, projects, fstab

        name = p["model"]
        if id == "recovery.architecture":
            return architecture.graph(model.report(name), flags.view(name))
        if id == "recovery.flags":
            return flags.view(name)
        if id == "recovery.flags.validate":
            return flags.validate(name)
        if id == "recovery.dependencies":
            return dependencies.validate(name)
        if id == "recovery.status":
            return projects.status(name)
        return fstab.report(model.report(name))
    if id == "recovery.acquire":
        from secripts.recovery.guidance import acquire

        return acquire(**p)
    if id == "recovery.build.diagnose":
        from secripts.recovery.diagnostics import diagnose

        return diagnose(p["artifact"], p.get("tree"))
    if id == "recovery.source":
        from secripts.recovery.planner import source_intelligence
        from secripts.recovery.workspace import load_workspace
        from secripts.safety import SecError

        try:
            workspace = {"root": p["workspace"]} if p.get("workspace") else load_workspace()
        except SecError:
            workspace = {}
        return source_intelligence(workspace)
    if id == "ai.context":
        from secripts.ai.context import preview

        return preview(p.get("artifact"))
    if id == "ai.providers":
        from secripts.ai.providers import catalog

        return catalog()
    raise ValueError("Unknown product operation")
