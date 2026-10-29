#!/usr/bin/env python3
"""Native Codex context transport using the shared resolver, without private contents."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
MAX_CHARS = 6000


def respond(event, message, warning=None):
    result = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": message[:MAX_CHARS]}}
    if warning:
        result["systemMessage"] = warning
    print(json.dumps(result, ensure_ascii=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", required=True)
    args = parser.parse_args()
    event = "SessionStart"
    try:
        payload = json.load(sys.stdin)
        event = payload.get("hook_event_name", "SessionStart")
        if event not in ("SessionStart", "SubagentStart"):
            raise ValueError("Unsupported lifecycle event")
        if not isinstance(payload.get("cwd"), str) or not Path(payload["cwd"]).is_absolute():
            raise ValueError("Missing absolute cwd; automatic context was not selected")
        cwd = Path(payload["cwd"]).resolve(strict=True)
        private_root = Path(args.private_root).expanduser().resolve(strict=True)
        source = private_root / "global/hooks/private_context.py"
        spec = importlib.util.spec_from_file_location("personal_ai_context", source)
        shared = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(shared)
        status, details = shared.resolve(cwd, private_root, canonical=True)
        prefix = "AI_PRIVATE_ROOT = " + str(private_root) + "\n"
        if status == "private-repo":
            context = private_root / private_root.name / "context.md"
            message = prefix + "Private configuration repository; no application context inferred.\n"
            if context.is_file():
                message += "Before significant configuration work read: " + str(context)
        else:
            if status == "project" and (details["private"].is_symlink() or
                                         details["private"].resolve().parent != private_root):
                raise ValueError("Private directory escapes the configured root")
            message = prefix + shared.build_message(status, details, cwd, private_root)
        if len(message) > MAX_CHARS:
            message = message[:MAX_CHARS - 150] + "\nInventory truncated; inspect the selected private directory only as needed."
        roles = ",".join(sorted(p.stem for p in (private_root / "global/agents").glob("*.md")))
        message += "\nGlobal Codex roles: personal-ai-{" + roles + "}. Prefer relevant project specialists."
        warning = "personal-AI-config: project is ambiguous; no private context selected" if status == "ambiguous" else None
        respond(event, message, warning)
    except Exception as exc:
        # Do not print payloads, tracebacks or the contents of private files.
        safe_event = event if event in ("SessionStart", "SubagentStart") else "SessionStart"
        warning = "personal-AI-config hook error: " + type(exc).__name__ + "; automatic context unavailable"
        respond(safe_event, warning + ". Resolve the explicit task project before reading private context.", warning)
    return 0  # Visible warning/context, rather than silently suppressing stdout on error.


if __name__ == "__main__":
    sys.exit(main())
