"""Conservative bounded build-log classification. Symptoms do not establish root cause."""

import hashlib
import re
from pathlib import Path
from secripts.images.artifacts import read
from secripts.secrets import sanitize_evidence

# Rules describe observable symptoms. Sources constrain suggestions, never confer certainty.
RULES = (
    (
        "SOURCE_API",
        r"error: (?:use of undeclared identifier|unknown type name|redefinition of)",
        "Compare recovery source, headers and dependency revisions; do not patch out declarations blindly.",
        "twrp-failure-312",
    ),
    (
        "SOONG_PANIC",
        r"panic in GenerateBuildActions|soong.*panic",
        "Inspect the first panic and source/module revisions; an nsjail warning is not proof of root cause.",
        "failure209",
    ),
    (
        "MISSING_MODULE",
        r"depends on undefined module|unrecognized module type|module .* not found",
        "Review namespace imports, device/common/vendor dependencies and the selected branch.",
        "soong",
    ),
    (
        "INVALID_PRODUCT",
        r"Cannot locate config makefile for product|Don't have a product spec|Invalid lunch combo|No such item in BRUNCH_MENU_CHOICES",
        "Compare AndroidProducts and PRODUCT_NAME with the configured lunch target.",
        "twrp-12",
    ),
    (
        "MISSING_INPUT",
        r"missing and no known rule to make it|No rule to make target|cannot find.*(?:dtb|dtbo|kernel)",
        "Identify the exact absent input and its declared dependency; do not suppress missing dependencies.",
        "twrp-failure-79",
    ),
    (
        "KERNEL_BUILD",
        r"(?:kernel/|kernel build).*error:|Error.*(?:Image.gz|vmlinux)",
        "Review kernel revision, config, toolchain and module/DTB relationships.",
        "kernel",
    ),
    (
        "VINTF",
        r"(?:ERROR|error|FAILED).*vintf|vintf.*(?:incompatible|not compatible)",
        "Compare device manifests, compatibility matrices and source generation.",
        "generic",
    ),
    (
        "SELINUX",
        r"neverallow.*(?:fail|violat)|libsepol.*error",
        "Review policy/source compatibility; do not disable enforcement as an automatic fix.",
        "generic",
    ),
    (
        "LINKER",
        r"undefined reference to|ld.lld: error:",
        "Review the first missing symbol, module dependencies and ABI/toolchain context.",
        "soong",
    ),
    (
        "JAVA",
        r"Unsupported class file major version|unsupported class version|JAVA_HOME is not set|Could not find java",
        "Inspect the checked-out build's JDK selection; host Java alone does not select source generation.",
        "host",
    ),
    (
        "PYTHON",
        r"python.*(?:not found|No such file)|SyntaxError: Missing parentheses in call to 'print'",
        "Check the interpreter required by this source generation; do not globally replace Python.",
        "host",
    ),
    (
        "DISK",
        r"No space left on device|Disk quota exceeded",
        "Inspect free bytes and inodes on the actual output filesystem; no automatic deletion.",
        "host",
    ),
    (
        "MEMORY",
        r"out of memory|cannot allocate memory|oom-kill",
        "Inspect bounded host/kernel evidence and concurrency; a bare 'Killed' line alone is inconclusive.",
        "host",
    ),
    (
        "MANIFEST",
        r"fatal:.*(?:manifest|revision).*not found|manifest.*(?:parse error|not found)",
        "Review manifest URL, revision and local manifests without silently updating them.",
        "manifest",
    ),
    (
        "HOST_TOOL",
        r"(?:command not found|Exec format error|Permission denied|nsjail error)",
        "Identify the exact host tool and environment boundary; do not assume it caused later failures.",
        "host",
    ),
)


def classify(text, *, tree=None):
    text = text[-65536:]
    from secripts.ai.context import clean

    text = clean(text)
    findings = []
    for id, pattern, action, source in RULES:
        hits = [line[:512] for line in text.splitlines() if re.search(pattern, line, re.I)][:4]
        if hits:
            findings.append(
                {
                    "classification": id,
                    "state": "INFERRED",
                    "confidence": "LIMITED",
                    "evidence": hits,
                    "suggested_action": action,
                    "research_source": source,
                    "root_cause": "UNRESOLVED",
                }
            )
    result = {
        "schema": 1,
        "status": "PARTIAL" if findings else "UNKNOWN",
        "findings": findings,
        "evidence": {"excerpt": text[-8192:], "bounded": True},
        "root_cause": "UNRESOLVED",
        "automatic_changes": False,
    }
    if tree:
        from secripts.recovery.planner import diagnose

        result["tree_context"] = diagnose(Path(tree))
    return sanitize_evidence(result)


def diagnose(path, tree=None):
    payload = read(Path(path), 2 * 1024**2)
    return {
        **classify(payload.decode("utf-8", errors="replace"), tree=tree),
        "log_sha256": hashlib.sha256(payload).hexdigest(),
        "log_bytes": len(payload),
    }
