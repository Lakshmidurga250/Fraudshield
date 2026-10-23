"""Reports actual verifiable Git repository metrics without fabrication."""

import subprocess


def run_git(args):
    try:
        res = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def main():
    print("=" * 60)
    print("  FRAUDSHIELD VERIFIED GIT REPOSITORY METRICS")
    print("=" * 60)

    # Commits count
    commit_count = run_git(["rev-list", "--count", "HEAD"])
    print(
        f"Total Commits:          {commit_count if not commit_count.startswith('Error') else '0 (Uncommitted repo)'}"
    )

    # Current branch
    branch = run_git(["branch", "--show-current"])
    print(f"Active Branch:          {branch}")

    # Contributors
    contributors = run_git(["shortlog", "-sn", "HEAD"])
    print("\nLocal Contributors:")
    if contributors and not contributors.startswith("Error"):
        for line in contributors.splitlines():
            print(f"  {line}")
    else:
        print("  No commits recorded yet.")

    # Recent log
    print("\nRecent 5 Commits:")
    log = run_git(["log", "-n", "5", "--oneline"])
    if log and not log.startswith("Error"):
        for line in log.splitlines():
            print(f"  {line}")
    else:
        print("  No commit history recorded yet.")
    print("=" * 60)


if __name__ == "__main__":
    main()
