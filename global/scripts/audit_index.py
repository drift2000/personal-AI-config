#!/usr/bin/env python3
"""Перевіряє файли в Git index на секрети та конфіденційні типи файлів.

    python audit_index.py [--repo <dir>] [--staged]

Без --staged перевіряє всі відстежувані файли (вміст з index), а також
файли, що відстежуються попри .gitignore. З --staged — лише staged зміни
(використовується в pre-commit). Код виходу 1, якщо є блокуючі знахідки.

Евристика не замінює уважного перегляду diff. Рядок із позначкою
`audit-allow` пропускається для загальних (generic) шаблонів.
"""
import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import PurePosixPath

MAX_BYTES = 1024 * 1024

FORBIDDEN_NAMES = [
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.kdbx",
    "id_rsa*", "id_ed25519*", "id_ecdsa*", "auth.json", ".credentials.json",
    "credentials*.json", "secrets.*", "*.sql", "*.sql.gz", "*.dump", "*.bak",
    "*.sqlite", "*.sqlite3", "*.db", "*.zip", "*.7z", "*.rar", "*.tar", "*.tgz", "*.tar.gz",
]
ALLOWED_NAMES = [".env.example"]

STRONG_PATTERNS = {
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "GitHub token": r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b",
    "Anthropic key": r"\bsk-ant-[A-Za-z0-9_-]{20,}",
    "OpenAI key": r"\bsk-(proj-)?[A-Za-z0-9_-]{32,}",
    "Slack token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    "Google API key": r"\bAIza[0-9A-Za-z_-]{35}\b",
    "URL with credentials": r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s:@]{3,}@",
}
GENERIC_PATTERNS = {
    "possible secret assignment":
        r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)\b"
        r"\s*[:=]\s*['\"]?(?![<{$])[^\s'\"<>]{8,}",
}


def git(repo, *args, binary=False):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace").strip())
    return out.stdout if binary else out.stdout.decode("utf-8", "replace")


def name_forbidden(path):
    name = PurePosixPath(path).name
    if name in ALLOWED_NAMES:
        return False
    if "local" in PurePosixPath(path).parts:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in FORBIDDEN_NAMES)


def scan(repo, staged):
    if staged:
        files = git(repo, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").split("\0")
    else:
        files = git(repo, "ls-files", "-z").split("\0")
    files = [f for f in files if f]

    blocking, warnings = [], []
    for path in files:
        if name_forbidden(path):
            blocking.append(f"{path}: заборонений тип/розташування файлу")
        blob = git(repo, "show", f":{path}", binary=True)
        if len(blob) > MAX_BYTES:
            blocking.append(f"{path}: розмір {len(blob)} байт > {MAX_BYTES}")
            continue
        if b"\0" in blob[:8000]:
            continue
        text = blob.decode("utf-8", "replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for label, pat in STRONG_PATTERNS.items():
                if re.search(pat, line):
                    blocking.append(f"{path}:{lineno}: {label}")
            if "audit-allow" in line:
                continue
            for label, pat in GENERIC_PATTERNS.items():
                if re.search(pat, line):
                    warnings.append(f"{path}:{lineno}: {label}")

    if not staged:
        ignored = git(repo, "ls-files", "-z", "--cached", "--ignored", "--exclude-standard").split("\0")
        for path in filter(None, ignored):
            blocking.append(f"{path}: відстежується, хоча підпадає під .gitignore")

    return len(files), blocking, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    try:
        count, blocking, warnings = scan(args.repo, args.staged)
    except RuntimeError as exc:
        print(f"audit_index: помилка git: {exc}", file=sys.stderr)
        return 2

    scope = "staged" if args.staged else "tracked"
    print(f"audit_index: перевірено {count} файл(ів) ({scope}).")
    for w in warnings:
        print(f"  WARN  {w}")
    for b in blocking:
        print(f"  BLOCK {b}")
    if blocking:
        print("Знайдено блокуючі проблеми. Приберіть файл з index (git rm --cached <file>) або виправте вміст."
              " Якщо секрет уже в історії — вважайте його скомпрометованим і замініть.")
        return 1
    if warnings:
        print("Попередження не блокують коміт — перегляньте їх вручну.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
