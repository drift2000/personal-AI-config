#!/usr/bin/env python3
"""SessionStart hook: знаходить приватний контекст активного проєкту.

Повідомляє лише шлях і перелік наявних матеріалів, не їхній вміст.
Якщо проєкт неможливо визначити однозначно, жодного контексту не підставляє.

Використання (Claude Code передає JSON у stdin, поле "cwd"):
    python private_context.py --private-root <path> [--cwd <dir>] [--plain]
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

RESERVED = {"global", "adapters"}
CASE_INSENSITIVE = os.name == "nt"
MAX_LISTED = 5


def norm(name):
    return name.casefold() if CASE_INSENSITIVE else name


def same_path(a, b):
    return norm(os.path.normpath(str(a))) == norm(os.path.normpath(str(b)))


def is_within(path, root):
    try:
        Path(norm(str(path))).relative_to(Path(norm(str(root))))
        return True
    except ValueError:
        return False


def git_toplevel(cwd):
    try:
        out = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return Path(out.stdout.strip()).resolve()


def private_projects(private_root):
    result = {}
    for d in private_root.iterdir():
        if d.is_dir() and not d.name.startswith(".") and d.name not in RESERVED:
            result[norm(d.name)] = d
    return result


def frontmatter(path):
    """Мінімальний парсер YAML-frontmatter: лише прості поля key: value."""
    data = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return data
    if not lines or lines[0].strip() != "---":
        return data
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip("'\"")
    return data


def canonical_git_root(cwd):
    """Return the main checkout for a linked worktree; never infer from branch names."""
    top = git_toplevel(cwd)
    if top is None:
        return None
    out = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--git-common-dir"],
                         capture_output=True, text=True, timeout=5)
    if out.returncode:
        raise ValueError("Cannot determine Git worktree identity")
    common = Path(out.stdout.strip())
    common = (cwd / common).resolve() if not common.is_absolute() else common.resolve()
    # Standard non-bare repositories: main checkout/.git. Otherwise fail closed.
    if common.name != ".git" or git_toplevel(common.parent) != common.parent:
        raise ValueError("Nonstandard Git common directory; explicit project identity required")
    return common.parent


def resolve(cwd, private_root, canonical=False):
    """Повертає (status, details). status: project | none | ambiguous | private-repo."""
    if is_within(cwd, private_root):
        return "private-repo", {}

    # Opt-in for Codex; the existing Claude entry point retains its old resolution.
    if canonical:
        root = canonical_git_root(cwd)
        if root is not None:
            if root == private_root:
                return "private-repo", {}
            if root.parent != private_root.parent:
                return "ambiguous", {"reason": "Git root is outside the configured project parent"}
            pdir = private_root / root.name
            if pdir.is_symlink():
                return "ambiguous", {"reason": "Private project directory is a symlink"}
            if pdir.is_dir():
                return "project", {"root": root, "private": pdir}
            return "none", {"root": root}

    projects = private_projects(private_root)
    sources_root = private_root.parent
    toplevel = git_toplevel(cwd)

    strong, weak = [], []
    for anc in [cwd, *cwd.parents]:
        pdir = projects.get(norm(anc.name))
        if not pdir:
            continue
        # Сильний збіг: конвенція <parent>/.private/<name> або корінь git-репозиторію.
        if same_path(anc.parent, sources_root) or (toplevel and same_path(anc, toplevel)):
            strong.append((anc, pdir))
        else:
            weak.append((anc, pdir))

    if len(strong) == 1:
        return "project", {"root": strong[0][0], "private": strong[0][1]}
    if len(strong) > 1:
        return "ambiguous", {"candidates": strong}

    if weak:
        return "ambiguous", {"candidates": weak}

    root = toplevel
    if root is None:
        for anc in [cwd, *cwd.parents]:
            if same_path(anc.parent, sources_root):
                root = anc
                break
    if root is None:
        return "ambiguous", {"reason": "cwd не належить жодному проєкту (корінь каталогу проєктів, workspace або поза ним)"}
    return "none", {"root": root}


def list_dir(path, pattern="*.md"):
    if not path.is_dir():
        return []
    return sorted(p.name for p in path.glob(pattern) if p.is_file())


def describe_skills(pdir):
    lines = []
    for base in (pdir / "skills", pdir / ".agents" / "skills"):
        if not base.is_dir():
            continue
        for skill in sorted(base.glob("*/SKILL.md")):
            fm = frontmatter(skill)
            name = fm.get("name", skill.parent.name)
            lines.append(f"- {name} — {fm.get('description', '(без опису)')}\n  SKILL.md: {skill}")
    return lines


def describe_agents(pdir):
    lines = []
    base = pdir / "agents"
    if base.is_dir():
        for agent in sorted(base.rglob("*.md")):
            fm = frontmatter(agent)
            lines.append(f"- {fm.get('name', agent.stem)} — {fm.get('description', '(без опису)')}\n  file: {agent}")
    return lines


def summarize(name, items):
    if not items:
        return None
    latest = ", ".join(items[-MAX_LISTED:])
    more = f" (останні {MAX_LISTED})" if len(items) > MAX_LISTED else ""
    return f"- {name}/: {len(items)} файл(ів){more}: {latest}"


def build_message(status, details, cwd, private_root):
    head = "[private-project-memory]"
    note_multi = ("Визначено лише за cwd сесії. Якщо задача явно вказує інший проєкт, "
                  "перевірте його корінь і використайте відповідний приватний контекст. "
                  "Уточнюйте проєкт лише якщо неоднозначність лишилася.")
    if status == "private-repo":
        return (f"{head} Сесія відкрита всередині приватного репозиторію ($AI_PRIVATE_ROOT = {private_root}). "
                "Усі файли тут приватні; не копіювати їх у робочі репозиторії чи зовнішні сервіси.")
    if status == "ambiguous":
        msg = [f"{head} Активний проєкт однозначно не визначено (cwd: {cwd}). Приватний контекст НЕ підставлено."]
        if details.get("reason"):
            msg.append(f"Причина: {details['reason']}.")
        for anc, pdir in details.get("candidates", []):
            msg.append(f"- кандидат: {anc} → {pdir}")
        msg.append("Якщо потрібен приватний контекст — перевірте явно заданий у задачі корінь проєкту; "
                   "спитайте користувача лише якщо проєкт досі неоднозначний.")
        msg.append(f"$AI_PRIVATE_ROOT = {private_root}")
        return "\n".join(msg)
    if status == "none":
        return (f"{head} Проєкт: {details['root'].name} (root: {details['root']}). "
                f"Приватного каталогу немає ($AI_PRIVATE_ROOT = {private_root}). "
                "Для значної роботи можна запропонувати створити його skill-ом private-project-memory; "
                f"автоматично не створювати.\n{note_multi}")

    pdir, root = details["private"], details["root"]
    msg = [
        f"{head} Активний проєкт: {root.name} (root: {root})",
        f"Приватний каталог: {pdir}",
        f"$AI_PRIVATE_ROOT = {private_root}",
        "Матеріали ПРИВАТНІ: не копіювати в репозиторій, коміти, PR чи зовнішні сервіси без явного дозволу.",
        "Наявне (вміст НЕ завантажено):",
    ]
    ctx = pdir / "context.md"
    msg.append(f"- context.md: {'є' if ctx.is_file() else 'немає'}")
    for sub in ("briefs", "decisions", "history"):
        line = summarize(sub, list_dir(pdir / sub))
        if line:
            msg.append(line)
    if (pdir / "archive").is_dir():
        msg.append("- archive/: є (читати лише на прохання)")
    skills = describe_skills(pdir)
    if skills:
        msg.append("Приватні skills проєкту (не зареєстровані в Claude; коли задача відповідає опису — прочитайте SKILL.md і виконуйте його інструкції):")
        msg.extend(skills)
    agents = describe_agents(pdir)
    if agents:
        msg.append("Приватні агенти проєкту (щоб використати — запустіть субагента загального призначення з тілом файлу як інструкцією):")
        msg.extend(agents)
    msg.append("Перед значною роботою прочитайте context.md, далі — лише релевантні файли (skill private-project-memory).")
    msg.append(note_multi)
    return "\n".join(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--cwd", help="перевизначити cwd (для тестів)")
    parser.add_argument("--plain", action="store_true", help="вивести текст замість JSON")
    args = parser.parse_args()

    cwd = args.cwd
    if not cwd and not sys.stdin.isatty():
        try:
            cwd = json.loads(sys.stdin.read() or "{}").get("cwd")
        except (ValueError, AttributeError):
            cwd = None
    cwd = Path(cwd or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    private_root = Path(os.path.expanduser(args.private_root)).resolve()

    if not private_root.is_dir():
        message = f"[private-project-memory] Приватний репозиторій не знайдено: {private_root}"
    else:
        status, details = resolve(cwd, private_root)
        message = build_message(status, details, cwd, private_root)

    sys.stdout.reconfigure(encoding="utf-8")
    if args.plain:
        print(message)
    else:
        # ASCII-JSON (\uXXXX): не залежить від кодування консолі Windows.
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                 "additionalContext": message}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
