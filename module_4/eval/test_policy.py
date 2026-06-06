"""Verify that the governance policy document and enforcement artifacts agree.

Run from the repository root:

    pytest eval/test_policy.py -v
"""

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

POLICY = REPO / "docs" / "governance-policy.md"
STORAGE_ALLOW = REPO / "mcp-servers" / "storage" / "allow-list.json"
RETRIEVAL_ALLOW = REPO / "mcp-servers" / "retrieval" / "allow-list.json"
RUN_AGENT = REPO / "scripts" / "run-agent.sh"
SKILLS_DIR = REPO / ".claude" / "skills"


def _subsection(chunk: str, title: str) -> str:
    """Return the text of a '### {title}' subsection within a role entry."""
    match = re.search(
        r"###\s+" + re.escape(title) + r"\s*\n(.*?)(?=\n###\s|\Z)",
        chunk,
        re.S,
    )
    return match.group(1) if match else ""


def parse_policy() -> dict[str, dict]:
    """Parse docs/governance-policy.md into role-level permissions."""
    text = POLICY.read_text(encoding="utf-8")
    roles: dict[str, dict] = {}

    # Each role entry starts with: ## Role: role-name
    for chunk in re.split(r"^##\s+Role:\s*", text, flags=re.M)[1:]:
        name = chunk.splitlines()[0].strip()

        entry = {
            "storage_ops": set(),
            "retrieve_granted": False,
            "retrieve_ceiling": None,
            "skills_permitted": set(),
            "workspace": None,
            "memory": None,
        }

        # MCP rows look like:
        # | write_entry | storage | YES | reason |
        mcp = _subsection(chunk, "MCP server and operation access")
        for op, server, granted in re.findall(
            r"^\|\s*([a-z_]+)\s*\|\s*([a-z]+)\s*\|\s*(YES|NO)\s*\|",
            mcp,
            re.M,
        ):
            if granted == "YES" and server == "storage":
                entry["storage_ops"].add(op)

            if granted == "YES" and server == "retrieval" and op == "retrieve":
                entry["retrieve_granted"] = True

        # Skill rows look like:
        # | run-tests | YES | reason |
        skills = _subsection(chunk, "Skill activation scope")
        for skill, granted in re.findall(
            r"^\|\s*([a-z0-9-]+)\s*\|\s*(YES|NO)\s*\|",
            skills,
            re.M,
        ):
            if granted == "YES":
                entry["skills_permitted"].add(skill)

        # Classification ceiling line looks like:
        # **Maximum level:** internal
        ceiling = re.search(r"\*\*Maximum level:\*\*\s*([a-z]+)", chunk)
        if ceiling:
            entry["retrieve_ceiling"] = ceiling.group(1)

        # Container permissions line looks like:
        # **Container permissions:** workspace read-write, memory mounted
        container = re.search(
            r"\*\*Container permissions:\*\*\s*"
            r"workspace\s+(read-only|read-write),\s*"
            r"memory\s+(mounted|omitted)",
            chunk,
        )
        if container:
            entry["workspace"] = {
                "read-only": "ro",
                "read-write": "rw",
            }[container.group(1)]

            entry["memory"] = {
                "mounted": True,
                "omitted": False,
            }[container.group(2)]

        roles[name] = entry

    return roles


def parse_run_agent() -> dict[str, dict]:
    """Parse scripts/run-agent.sh into role-level container permissions."""
    text = RUN_AGENT.read_text(encoding="utf-8")
    modes: dict[str, dict] = {}

    # Case branches look like:
    #
    # implementer|orchestrator)
    #   WORKSPACE_MODE="rw"
    #   MOUNT_MEMORY=1
    #   ;;
    for pattern, body in re.findall(
        r"^\s*([a-z|_-]+)\)\s*\n(.*?);;",
        text,
        re.S | re.M,
    ):
        mode = re.search(r'WORKSPACE_MODE="(ro|rw)"', body)
        memory = re.search(r"MOUNT_MEMORY=(0|1)", body)

        if not mode or not memory:
            continue

        for role in pattern.split("|"):
            role = role.strip()
            modes[role] = {
                "workspace": mode.group(1),
                "memory": memory.group(1) == "1",
            }

    return modes


def parse_skill(path: Path) -> set[str]:
    """Return the set of roles permitted by a skill file.

    Expected line in each skill file:

        **Permitted roles:** implementer, tester

    Use "none" when no roles are permitted.
    """
    text = path.read_text(encoding="utf-8")
    permitted = re.search(r"\*\*Permitted roles:\*\*\s*(.+)", text)

    if not permitted:
        return set()

    roles = {role.strip() for role in permitted.group(1).split(",") if role.strip()}

    return set() if roles == {"none"} else roles


def load_json(path: Path) -> dict:
    """Read a JSON file and fail clearly if it is missing or invalid."""
    assert path.exists(), f"{path.relative_to(REPO)} is missing"
    return json.loads(path.read_text(encoding="utf-8"))


POLICY_ROLES = parse_policy()
STORAGE_ALLOW_DATA = load_json(STORAGE_ALLOW)
RETRIEVAL_ALLOW_DATA = load_json(RETRIEVAL_ALLOW).get("retrieve", {})
RUN_AGENT_MODES = parse_run_agent()
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))
ROLE_NAMES = sorted(POLICY_ROLES.keys())


def test_policy_document_parsed():
    """A parsing failure should look like a parsing failure, not an empty pass."""
    assert ROLE_NAMES, "No role entries were parsed from docs/governance-policy.md."


def test_skill_files_found():
    """The skill-scope test should not pass merely because no skill files were found."""
    assert SKILL_FILES, "No skill files were found under .claude/skills/*/SKILL.md."


def test_allowlist_files_present_in_repo():
    """The allow-lists must be committed files, not generated only at runtime."""
    assert STORAGE_ALLOW.exists(), "mcp-servers/storage/allow-list.json is missing"
    assert RETRIEVAL_ALLOW.exists(), "mcp-servers/retrieval/allow-list.json is missing"


@pytest.mark.parametrize("role", ROLE_NAMES)
def test_storage_allowlist_matches_policy(role: str):
    """The storage allow-list grants each role exactly its policy operations."""
    policy_ops = POLICY_ROLES[role]["storage_ops"]
    allow_ops = {op for op, roles in STORAGE_ALLOW_DATA.items() if role in roles}

    assert allow_ops == policy_ops, (
        f"{role}: storage allow-list grants {sorted(allow_ops)}, "
        f"policy grants {sorted(policy_ops)}"
    )


@pytest.mark.parametrize("role", ROLE_NAMES)
def test_no_storage_overgrant(role: str):
    """No allow-list may grant a role an operation its policy does not grant."""
    policy_ops = POLICY_ROLES[role]["storage_ops"]
    allow_ops = {op for op, roles in STORAGE_ALLOW_DATA.items() if role in roles}

    overgranted = allow_ops - policy_ops

    assert not overgranted, (
        f"{role}: allow-list grants {sorted(overgranted)} " f"not permitted by policy"
    )


@pytest.mark.parametrize("role", ROLE_NAMES)
def test_retrieval_grant_matches_policy(role: str):
    """The retrieval grant and classification ceiling must match the policy."""
    rule = RETRIEVAL_ALLOW_DATA.get(role)
    granted = bool(rule and rule.get("granted"))

    assert (
        granted == POLICY_ROLES[role]["retrieve_granted"]
    ), f"{role}: retrieve grant disagrees with policy"

    if granted:
        assert (
            rule.get("classification_ceiling") == POLICY_ROLES[role]["retrieve_ceiling"]
        ), (
            f"{role}: classification ceiling disagrees with policy. "
            f"allow-list says {rule.get('classification_ceiling')}, "
            f"policy says {POLICY_ROLES[role]['retrieve_ceiling']}"
        )


@pytest.mark.parametrize("skill_path", SKILL_FILES, ids=lambda path: path.parent.name)
def test_skill_scope_matches_policy(skill_path: Path):
    """Each skill file permits exactly the roles the policy permits."""
    skill = skill_path.parent.name

    permitted_in_file = parse_skill(skill_path)
    permitted_in_policy = {
        role for role, data in POLICY_ROLES.items() if skill in data["skills_permitted"]
    }

    assert permitted_in_file == permitted_in_policy, (
        f"{skill}: skill file permits {sorted(permitted_in_file)}, "
        f"policy permits {sorted(permitted_in_policy)}"
    )


@pytest.mark.parametrize("role", ROLE_NAMES)
def test_container_permissions_match_policy(role: str):
    """The startup script's workspace and memory settings must match the policy."""
    policy_mode = {
        "workspace": POLICY_ROLES[role]["workspace"],
        "memory": POLICY_ROLES[role]["memory"],
    }

    assert (
        policy_mode["workspace"] is not None
    ), f"{role}: policy has no workspace setting in its Container permissions line"
    assert (
        policy_mode["memory"] is not None
    ), f"{role}: policy has no memory setting in its Container permissions line"

    assert (
        role in RUN_AGENT_MODES
    ), f"{role}: scripts/run-agent.sh has no explicit permission branch for this role"

    assert RUN_AGENT_MODES[role] == policy_mode, (
        f"{role}: run-agent.sh uses {RUN_AGENT_MODES[role]}, "
        f"policy says {policy_mode}"
    )
