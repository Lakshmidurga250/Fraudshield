"""Accurately measures lines of code across project source files.

Differentiates:
- Raw LOC: Total lines in source files
- Code LOC: Non-blank, non-comment lines
- Comment LOC: Lines containing comments
- Blank LOC: Empty/whitespace lines

Excludes:
- Virtual environments (.venv, env)
- Binary artifacts (.joblib, .db)
- Datasets (.csv)
- Caches (__pycache__, .pytest_cache, .ruff_cache)
- Git directory (.git)
"""

import os
from pathlib import Path
from typing import Dict

EXTENSIONS = {".py", ".html", ".css", ".js", ".md", ".toml", ".yml", ".yaml"}
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "instance",
    "models",
    "datasets",
    "htmlcov",
    "build",
    "dist",
}


def count_file_lines(file_path: Path) -> Dict[str, int]:
    raw_count = 0
    blank_count = 0
    comment_count = 0
    code_count = 0

    suffix = file_path.suffix.lower()

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                raw_count += 1
                stripped = line.strip()
                if not stripped:
                    blank_count += 1
                elif suffix in (".py", ".toml", ".yml", ".yaml") and stripped.startswith("#"):
                    comment_count += 1
                elif suffix in (".js", ".css") and (
                    stripped.startswith("//")
                    or stripped.startswith("/*")
                    or stripped.startswith("*")
                ):
                    comment_count += 1
                elif suffix == ".html" and (
                    stripped.startswith("<!--") or stripped.startswith("{#")
                ):
                    comment_count += 1
                else:
                    code_count += 1
    except Exception:
        pass

    return {
        "raw": raw_count,
        "blank": blank_count,
        "comment": comment_count,
        "code": code_count,
    }


def main():
    root = Path(__file__).resolve().parent.parent

    total_stats = {"raw": 0, "blank": 0, "comment": 0, "code": 0}
    by_extension: Dict[str, Dict[str, int]] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            ext = file_path.suffix.lower()

            if ext in EXTENSIONS:
                stats = count_file_lines(file_path)
                for k in total_stats:
                    total_stats[k] += stats[k]

                if ext not in by_extension:
                    by_extension[ext] = {"files": 0, "raw": 0, "code": 0, "comment": 0, "blank": 0}
                by_extension[ext]["files"] += 1
                for k in ("raw", "code", "comment", "blank"):
                    by_extension[ext][k] += stats[k]

    print("=" * 68)
    print("  FRAUDSHIELD VERIFIABLE CODEBASE SCALE & LOC MEASUREMENT REPORT")
    print("=" * 68)
    print(
        f"{'Extension':<12} | {'Files':<6} | {'Code LOC':<10} | {'Comments':<10} | {'Blanks':<8} | {'Raw LOC':<8}"
    )
    print("-" * 68)
    for ext, s in sorted(by_extension.items(), key=lambda x: x[1]["code"], reverse=True):
        print(
            f"{ext:<12} | {s['files']:<6} | {s['code']:<10} | {s['comment']:<10} | {s['blank']:<8} | {s['raw']:<8}"
        )
    print("-" * 68)
    print(
        f"{'TOTAL':<12} | {sum(s['files'] for s in by_extension.values()):<6} | "
        f"{total_stats['code']:<10} | {total_stats['comment']:<10} | "
        f"{total_stats['blank']:<8} | {total_stats['raw']:<8}"
    )
    print("=" * 68)
    print("Counting Methodology: Non-blank, non-comment lines of code in verified project sources.")
    print(
        "Excludes: Virtual environments, binary models (.joblib), CSV datasets, test caches, build artifacts."
    )


if __name__ == "__main__":
    main()
