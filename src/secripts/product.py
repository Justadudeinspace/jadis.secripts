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
