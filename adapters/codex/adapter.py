"""Codex-only installation transactions. No credentials/config.toml access or edits."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import tempfile
import uuid

SCHEMA = 1
NAME = r"[a-z0-9]+(?:-[a-z0-9]+)*"


class Conflict(ValueError):
    pass


def role_sources(repo):
    """Roles are shared with Claude: name/description come from global/agents/*.md."""
    roles = []
    for source in sorted((repo / "global/agents").glob("*.md")):
        head = re.match(r"---\n(.*?)\n---", source.read_text(encoding="utf-8"), re.S)
        fields = dict(re.findall(r"(?m)^(name|description):\s*(.+?)\s*$", head.group(1) if head else ""))
        if not re.fullmatch(NAME, source.stem) or fields.get("name") != source.stem or not fields.get("description"):
            raise Conflict("Role needs frontmatter name matching file and description: " + str(source))
        roles.append((source.stem, fields["description"], source))
    if not roles:
        raise Conflict("No role sources in global/agents")
    return roles


def absolute(path):
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parents_safe(path):
    # Do not follow a foreign parent symlink into a different profile/project.
    for parent in path.parents:
        if parent.is_symlink():
            raise Conflict("Symlink in destination ancestry: " + str(parent))
        if parent.exists() and not parent.is_dir():
            raise Conflict("Non-directory parent: " + str(parent))


def snapshot(path):
    if path.is_symlink():
        return {"kind": "link", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "absent"}
    mode = stat.S_IMODE(path.stat().st_mode)
    if path.is_file():
        return {"kind": "file", "sha256": digest(path.read_bytes()), "mode": mode}
    if path.is_dir():
        return {"kind": "directory", "mode": mode,
                "children": {p.name: snapshot(p) for p in sorted(path.iterdir())}}
    raise Conflict("Unsupported filesystem object: " + str(path))


def desired(spec):
    if "target" in spec:
        return {"kind": "link", "target": spec["target"]}
    return {"kind": "file", "sha256": digest(spec["text"].encode()), "mode": 0o600}


def specifications(repo, codex_home, user_home, python):
    if os.name != "posix":
        raise Conflict("Codex symlink adapter currently supports POSIX only; Claude is unchanged.")
    specs = [{"id": "AGENTS.md", "path": str(codex_home / "AGENTS.md"),
              "target": str(repo / "global/AGENTS.md")}]
    for role, description, source in role_sources(repo):
        # Transport instructions only; role bodies stay in global/agents/.
        instructions = (
            "AI_PRIVATE_ROOT = " + str(repo) + "\n"
            "Global AGENTS.md is already loaded; do not re-read it. "
            "Before acting, read the role body " + str(source) + " and apply it with the relevant "
            "project instructions/accepted ADRs. Claude frontmatter tools do not grant Codex permissions. "
            "If the role file cannot be read, report the missing instructions before proceeding.")
        text = ("# personal-AI-config: transport wrapper, not a copy of the role\n"
                "name = " + json.dumps("personal-ai-" + role) + "\n"
                "description = " + json.dumps(description) + "\n"
                "developer_instructions = " + json.dumps(instructions, ensure_ascii=False) + "\n")
        specs.append({"id": "role:" + role,
                      "path": str(codex_home / "agents" / ("personal-ai-" + role + ".toml")), "text": text})
    manifests = sorted((repo / "global/skills").glob("*/SKILL.md"))
    names = set()
    for manifest in manifests:
        name = manifest.parent.name
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            raise Conflict("Invalid skill directory name: " + name)
        match = re.search(r"(?m)^name:\s*[\"']?([a-z0-9-]+)[\"']?\s*$", manifest.read_text())
        if not match or match.group(1) != name or name in names:
            raise Conflict("Skill name must be unique and match directory: " + str(manifest))
        names.add(name)
        specs.append({"id": "skill:" + name, "path": str(user_home / ".agents/skills" / name),
                      "target": str(manifest.parent)})
    command = " ".join(shlex.quote(str(p)) for p in
                       [python, "-B", repo / "adapters/codex/context_hook.py", "--private-root", repo])
    hooks = {"description": "personal-AI-config context discovery (no document content)", "hooks": {
        event: [{"hooks": [{"type": "command", "command": command, "timeout": 15}]}]
        for event in ("SessionStart", "SubagentStart")}}
    specs.append({"id": "hooks.json", "path": str(codex_home / "hooks.json"), "text": encode(hooks)})
    for spec in specs:
        if "target" in spec and not Path(spec["target"]).exists():
            raise Conflict("Missing source: " + spec["target"])
    receipt = {"schema": SCHEMA, "source": str(repo),
               "objects": {s["path"]: desired(s) for s in specs}}
    specs.append({"id": "receipt", "path": str(codex_home / ".personal-ai-config/receipt.json"),
                  "text": encode(receipt)})
    return specs


def replacement_safe(spec, before):
    # Explicit migration is deliberately narrow. Never back up config/auth/history.
    if spec["id"] == "AGENTS.md":
        return before["kind"] in ("file", "link")
    if spec["id"] == "skill:private-project-memory":
        if before["kind"] == "link":
            return True
        # A one-file directory may still contain unrelated user instructions.
        # Replace an unpacked skill only when its complete snapshot matches the
        # shared source; child-name checks alone do not protect its contents.
        return before["kind"] == "directory" and before == snapshot(Path(spec["target"]))
    return False


def duplicate_skills(repo, user_home, codex_home):
    """Detect user-level duplicate manifests, without scanning system/plugin skills."""
    expected = {p.parent.name: user_home / ".agents/skills" / p.parent.name / "SKILL.md"
                for p in (repo / "global/skills").glob("*/SKILL.md")}
    conflicts = []
    for base in (user_home / ".agents/skills", codex_home / "skills"):
        if not base.is_dir():
            continue
        for folder in base.iterdir():
            if folder.name.startswith(".") or not folder.is_dir():
                continue
            manifest = folder / "SKILL.md"
            if not manifest.is_file():
                continue
            match = re.search(r"(?m)^name:\s*[\"']?([a-z0-9-]+)[\"']?\s*$", manifest.read_text())
            if match and match.group(1) in expected and manifest != expected[match.group(1)]:
                conflicts.append("Duplicate user skill: " + str(manifest))
    return conflicts


def plan(repo, codex_home, user_home, python, replacements=()):
    for destination in (codex_home, user_home / ".agents/skills"):
        if destination == repo or repo in destination.parents:
            raise Conflict("Profile targets must be outside the source repository")
    specs = specifications(repo, codex_home, user_home, python)
    permitted = {"AGENTS.md", "skill:private-project-memory"}
    if set(replacements) - permitted:
        raise Conflict("Only AGENTS.md and skill:private-project-memory support explicit migration.")
    conflicts = duplicate_skills(repo, user_home, codex_home)
    override = codex_home / "AGENTS.override.md"
    if os.path.lexists(override):
        conflicts.append("AGENTS.override.md can shadow the global symlink: " + str(override))
    receipt_path = codex_home / ".personal-ai-config/receipt.json"
    parents_safe(receipt_path)
    owned = {}
    if receipt_path.exists():
        if receipt_path.is_symlink():
            raise Conflict("Receipt must not be a symlink")
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("schema") != SCHEMA or receipt.get("source") != str(repo):
            raise Conflict("Foreign ownership receipt")
        owned = receipt.get("objects", {})
    entries = []
    for spec in specs:
        parents_safe(Path(spec["path"]))
        before = snapshot(Path(spec["path"]))
        after = desired(spec)
        action = "keep" if before == after else "create" if before["kind"] == "absent" else "replace"
        if action == "replace":
            managed = before == owned.get(spec["path"]) or (spec["id"] == "receipt" and bool(owned))
            authorized = spec["id"] in replacements and replacement_safe(spec, before)
            if not managed and not authorized:
                conflicts.append("Foreign or modified object: " + spec["path"])
        entries.append(dict(spec, before=before, after=after, action=action))
    return {"schema": SCHEMA, "repo": str(repo), "codex_home": str(codex_home),
            "user_home": str(user_home), "python": str(python),
            "replacements": list(replacements), "entries": entries, "conflicts": conflicts}


def save_new(path, data):
    parents_safe(path)
    with path.open("x", encoding="utf-8") as out:
        os.chmod(path, 0o600)
        out.write(encode(data))


def atomic_json(path, data):
    fd, name = tempfile.mkstemp(prefix=".personal-ai-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(encode(data))
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.lexists(name):
            os.unlink(name)


def make_parents(path, created):
    absent = []
    parent = path.parent
    while not parent.exists():
        absent.append(parent)
        parent = parent.parent
    for directory in reversed(absent):
        directory.mkdir(mode=0o700)
        created.append(str(directory))


def copy_object(source, target):
    if source.is_symlink():
        target.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target)


def remove_object(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def install_object(entry):
    path = Path(entry["path"])
    temporary = path.with_name(".personal-ai-" + uuid.uuid4().hex)
    displaced = path.with_name(".personal-ai-displaced-" + uuid.uuid4().hex)
    try:
        if "target" in entry:
            temporary.symlink_to(entry["target"], target_is_directory=Path(entry["target"]).is_dir())
        else:
            with temporary.open("x", encoding="utf-8") as out:
                os.chmod(temporary, 0o600)
                out.write(entry["text"])
        if entry["before"]["kind"] == "directory":
            os.replace(path, displaced)
        try:
            os.replace(temporary, path)
        except Exception:
            if displaced.exists() and not os.path.lexists(path):
                os.replace(displaced, path)
            raise
        if displaced.exists():
            shutil.rmtree(displaced)
    finally:
        if os.path.lexists(temporary):
            temporary.unlink()


def validate_manifest(manifest, path, repo):
    if manifest.get("schema") != SCHEMA or manifest.get("repo") != str(repo):
        raise Conflict("Manifest source/schema mismatch")
    home = absolute(manifest["codex_home"])
    user = absolute(manifest["user_home"])
    if path.parent.parent != home / ".personal-ai-config/backups":
        raise Conflict("Manifest must be inside the recorded profile backup directory")
    # Recovery must remain possible even when linked source files were removed.
    allowed = {"AGENTS.md": home / "AGENTS.md", "hooks.json": home / "hooks.json",
               "receipt": home / ".personal-ai-config/receipt.json"}
    seen = set()
    for entry in manifest["entries"]:
        identifier = entry["id"]
        expected = allowed.get(identifier)
        kind, _, name = identifier.partition(":")
        if kind in ("skill", "role") and re.fullmatch(NAME, name):
            expected = (user / ".agents/skills" / name if kind == "skill"
                        else home / "agents" / ("personal-ai-" + name + ".toml"))
        if (expected is None or entry["path"] != str(expected) or entry["path"] in seen
                or desired(entry) != entry["after"]):
            raise Conflict("Unexpected rollback target")
        seen.add(entry["path"])
        parents_safe(Path(entry["path"]))
        if "backup" in entry and not re.fullmatch(r"original-\d+", entry["backup"]):
            raise Conflict("Invalid backup reference")
    allowed_parents = {str(p) for e in manifest["entries"] for p in Path(e["path"]).parents}
    if set(manifest.get("created_dirs", [])) - allowed_parents:
        raise Conflict("Unexpected directory in rollback manifest")


def rollback(path, repo):
    parents_safe(path)
    if path.is_symlink():
        raise Conflict("Manifest must not be a symlink")
    manifest = json.loads(path.read_text())
    validate_manifest(manifest, path, repo)
    if manifest["status"] == "rolled-back":
        return
    # Validate EVERYTHING before restoring anything, including modified backup copies.
    for entry in manifest["entries"]:
        actual = snapshot(Path(entry["path"]))
        if actual not in (entry["before"], entry["after"]):
            raise Conflict("Changed since installation; rollback refused: " + entry["path"])
        if entry["before"]["kind"] != "absent":
            backup = path.parent / entry["backup"]
            if snapshot(backup) != entry["before"]:
                raise Conflict("Missing or modified backup: " + str(backup))
    for entry in reversed(manifest["entries"]):
        target = Path(entry["path"])
        if snapshot(target) == entry["before"]:
            continue
        remove_object(target)
        if entry["before"]["kind"] != "absent":
            copy_object(path.parent / entry["backup"], target)
    # Never remove nonempty directories or anything outside recorded target ancestry.
    for directory in reversed(manifest.get("created_dirs", [])):
        try:
            Path(directory).rmdir()
        except OSError:
            pass
    manifest["status"] = "rolled-back"
    atomic_json(path, manifest)


def activate(prepared, repo):
    if prepared.get("schema") != SCHEMA or prepared.get("repo") != str(repo):
        raise Conflict("Plan source/schema mismatch")
    current = plan(repo, absolute(prepared["codex_home"]), absolute(prepared["user_home"]),
                   prepared["python"], prepared["replacements"])
    if current != prepared:
        raise Conflict("Plan is stale or edited; prepare and review again")
    if current["conflicts"]:
        raise Conflict("Preflight conflicts: " + "; ".join(current["conflicts"]))
    changed = [e for e in current["entries"] if e["action"] != "keep"]
    if not changed:
        return None
    backup_dir = absolute(current["codex_home"]) / ".personal-ai-config/backups" / uuid.uuid4().hex
    parents_safe(backup_dir)
    backup_dir.mkdir(parents=True, mode=0o700)
    os.chmod(backup_dir.parent, 0o700)
    manifest_path = backup_dir / "manifest.json"
    manifest = {k: current[k] for k in ("schema", "repo", "codex_home", "user_home", "python")}
    manifest.update(status="preparing", entries=[], created_dirs=[])
    for i, original in enumerate(changed):
        entry = dict(original)
        if entry["before"]["kind"] != "absent":
            entry["backup"] = "original-" + str(i)
            copy_object(Path(entry["path"]), backup_dir / entry["backup"])
            if snapshot(backup_dir / entry["backup"]) != entry["before"]:
                raise Conflict("Object changed while backing up: " + entry["path"])
        manifest["entries"].append(entry)
    save_new(manifest_path, manifest)
    try:
        for entry in manifest["entries"]:
            if snapshot(Path(entry["path"])) != entry["before"]:
                raise Conflict("Object changed after preflight: " + entry["path"])
        manifest["status"] = "applying"
        atomic_json(manifest_path, manifest)
        for entry in manifest["entries"]:
            parents_safe(Path(entry["path"]))
            make_parents(Path(entry["path"]), manifest["created_dirs"])
            atomic_json(manifest_path, manifest)
            install_object(entry)
        manifest["status"] = "active"
        atomic_json(manifest_path, manifest)
    except Exception:
        try:
            rollback(manifest_path, repo)
        except Exception as exc:
            raise Conflict("Recovery required via " + str(manifest_path) + ": " + str(exc))
        raise
    return manifest_path


def run(args, repo):
    if args.activate:
        result = activate(json.loads(absolute(args.activate).read_text()), repo)
        print("Unchanged." if result is None else "Activated. Rollback manifest: " + str(result))
        return 0
    if args.rollback:
        rollback(absolute(args.rollback), repo)
        print("Rolled back; backup manifest retained.")
        return 0
    user_home = absolute(args.home or Path.home())
    # --home isolates both profile and user skill discovery, ignoring ambient CODEX_HOME.
    codex_home = absolute(args.codex_home or
                          (user_home / ".codex" if args.home else os.environ.get("CODEX_HOME", user_home / ".codex")))
    prepared = plan(repo, codex_home, user_home, args.python, args.replace)
    for entry in prepared["entries"]:
        print(entry["action"].upper(), entry["id"], entry["path"])
    for problem in prepared["conflicts"]:
        print("CONFLICT", problem)
    print("Untouched: config.toml, permission/trust/MCP/plugin settings, Claude, Git hooks, project files.")
    if args.prepare:
        save_new(absolute(args.prepare), prepared)
        print("Prepared only: " + str(absolute(args.prepare)))
    if prepared["conflicts"]:
        return 1
    if args.check and any(e["action"] != "keep" for e in prepared["entries"]):
        return 1
    return 0
