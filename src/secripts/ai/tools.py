"""Local typed context tools. AI responses cannot invoke these or an operation executor."""

from secripts.safety import SecError


def invoke(name, argument=""):
    from secripts.registry import registry

    if name == "registry.search":
        return [op.metadata() for op in registry().search(argument)][:12]
    if name == "registry.show":
        return registry().get(argument).metadata()
    if name == "receipt.summary":
        from secripts.receipts import summary, load

        return summary(load(argument))
    raise SecError(
        "AI tool refused: only registry metadata and explicit receipt summaries are allowed", 4
    )
