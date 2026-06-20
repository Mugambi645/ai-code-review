"""
Diff parser and code analyzer.
Parses unified diffs and extracts structured information for review.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import NullFormatter


@dataclass
class DiffHunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str] = field(default_factory=list)


@dataclass
class FileDiff:
    filename: str
    old_filename: str
    status: str  # added | modified | deleted | renamed
    hunks: list[DiffHunk] = field(default_factory=list)
    language: Optional[str] = None

    @property
    def added_lines(self) -> list[tuple[int, str]]:
        result = []
        for hunk in self.hunks:
            line_num = hunk.new_start
            for line in hunk.lines:
                if line.startswith("+"):
                    result.append((line_num, line[1:]))
                if not line.startswith("-"):
                    line_num += 1
        return result

    @property
    def removed_lines(self) -> list[tuple[int, str]]:
        result = []
        for hunk in self.hunks:
            line_num = hunk.old_start
            for line in hunk.lines:
                if line.startswith("-"):
                    result.append((line_num, line[1:]))
                if not line.startswith("+"):
                    line_num += 1
        return result

    def to_review_text(self) -> str:
        """Format diff for LLM consumption."""
        lines = [f"File: {self.filename} ({self.status})"]
        if self.language:
            lines.append(f"Language: {self.language}")
        lines.append("")
        for hunk in self.hunks:
            lines.append(
                f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@"
            )
            for line in hunk.lines:
                lines.append(line)
        return "\n".join(lines)


def detect_language(filename: str) -> Optional[str]:
    """Detect programming language from filename."""
    try:
        lexer = get_lexer_for_filename(filename)
        return lexer.name
    except Exception:
        return None


def parse_diff(raw_diff: str) -> list[FileDiff]:
    """Parse a unified diff string into structured FileDiff objects."""
    files: list[FileDiff] = []
    current_file: Optional[FileDiff] = None
    current_hunk: Optional[DiffHunk] = None

    for line in raw_diff.splitlines():
        # New file diff
        if line.startswith("diff --git"):
            if current_file:
                if current_hunk:
                    current_file.hunks.append(current_hunk)
                files.append(current_file)
            current_file = None
            current_hunk = None

        elif line.startswith("--- "):
            old_name = line[4:].strip()
            if old_name.startswith("a/"):
                old_name = old_name[2:]

        elif line.startswith("+++ "):
            new_name = line[4:].strip()
            if new_name.startswith("b/"):
                new_name = new_name[2:]
            status = "added" if old_name == "/dev/null" else "modified"
            if new_name == "/dev/null":
                status = "deleted"
                new_name = old_name
            current_file = FileDiff(
                filename=new_name,
                old_filename=old_name if old_name != "/dev/null" else new_name,
                status=status,
                language=detect_language(new_name),
            )

        elif line.startswith("@@") and current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                current_hunk = DiffHunk(
                    old_start=int(match.group(1)),
                    old_count=int(match.group(2) or 1),
                    new_start=int(match.group(3)),
                    new_count=int(match.group(4) or 1),
                )

        elif current_hunk is not None and (
            line.startswith("+") or line.startswith("-") or line.startswith(" ")
        ):
            current_hunk.lines.append(line)

    # Flush last file/hunk
    if current_file:
        if current_hunk:
            current_file.hunks.append(current_hunk)
        files.append(current_file)

    return files


def build_review_context(files: list[FileDiff], pr_title: str, pr_body: str) -> str:
    """Build the full context string sent to the LLM."""
    parts = [
        f"PR Title: {pr_title}",
        f"PR Description: {pr_body or 'No description provided.'}",
        "",
        f"Files changed: {len(files)}",
        "",
    ]
    for f in files:
        parts.append(f.to_review_text())
        parts.append("")

    return "\n".join(parts)
