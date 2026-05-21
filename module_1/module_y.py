"""
Formatting and reporting utilities for the parallel agent-session example.

This module is intentionally correct but lightly documented. It is designed for
the "Session B" agent task: improve docstrings in this file and update README.md,
without modifying any test files.
"""

from __future__ import annotations


def format_currency(amount: float) -> str:
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def build_report_title(project_name: str, version: str) -> str:
    clean_project = " ".join(project_name.strip().split())
    clean_version = version.strip()

    if not clean_project:
        clean_project = "Untitled Project"
    if not clean_version:
        clean_version = "draft"

    return f"{clean_project} — {clean_version}"


def mask_email(email: str) -> str:
    email = email.strip()
    if "@" not in email:
        raise ValueError("email must contain @")

    local_part, domain = email.split("@", 1)
    if not local_part or not domain:
        raise ValueError("email must include a local part and domain")

    if len(local_part) == 1:
        masked_local = "*"
    elif len(local_part) == 2:
        masked_local = local_part[0] + "*"
    else:
        masked_local = local_part[0] + "*" * (len(local_part) - 2) + local_part[-1]

    return f"{masked_local}@{domain.lower()}"


def generate_summary_line(name: str, status: str, score: int) -> str:
    display_name = " ".join(name.strip().split()).title()
    display_status = status.strip().lower().replace("_", " ")

    if not display_name:
        display_name = "Unknown"

    return f"{display_name}: {display_status} ({score})"


def create_markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    if not columns:
        raise ValueError("columns cannot be empty")

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"

    body_lines = []
    for row in rows:
        values = [str(row.get(column, "")) for column in columns]
        body_lines.append("| " + " | ".join(values) + " |")

    return "\n".join([header, separator, *body_lines])


def truncate_text(text: str, max_length: int = 80) -> str:
    if max_length < 4:
        raise ValueError("max_length must be at least 4")

    clean_text = " ".join(text.strip().split())
    if len(clean_text) <= max_length:
        return clean_text

    return clean_text[: max_length - 3].rstrip() + "..."
