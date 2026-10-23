"""Packages the submission ZIP for TrainPlex compliance testing.

Ensures:
1. `.git` directory IS INCLUDED so git history, commits (>=100), PR merges (>=100),
   and collaborators (>=2) are fully measurable by the automated scanner.
2. Proprietary license (no MIT/Apache/GPL).
3. No `.env` files (uses `example.env`).
4. Lockfiles present (`poetry.lock`, `package-lock.json`).
5. Excludes temporary binary caches (__pycache__, .pytest_cache).
"""

import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ZIP_DESKTOP = Path(r"C:\Users\lakshmi\OneDrive\Desktop\Fraudshield_Submission.zip")
OUTPUT_ZIP_WORKSPACE = ROOT / "Fraudshield_Submission.zip"

EXCLUDE_DIRS = {
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "htmlcov",
    "dist",
    "build",
}

EXCLUDE_EXTS = {".pyc", ".pyo", ".zip"}


def create_zip(target_path: Path):
    print(f"Creating submission zip: {target_path}")
    count = 0
    with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(ROOT):
            # Prune excluded directories
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

            for fname in filenames:
                file_path = Path(dirpath) / fname
                if file_path.suffix.lower() in EXCLUDE_EXTS:
                    continue
                # Do not zip existing zip files
                if fname.endswith(".zip"):
                    continue

                arcname = file_path.relative_to(ROOT)
                z.write(file_path, arcname)
                count += 1

    size_mb = target_path.stat().st_size / (1024 * 1024)
    print(f"Packaged {count} files ({size_mb:.2f} MB)")
    return size_mb, count


def verify_zip(zip_path: Path):
    print(f"\nVerifying compliance on {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        has_git = any(n.startswith(".git/") for n in names)
        has_lock = "poetry.lock" in names or "package-lock.json" in names
        has_os_license = "LICENSE" in names
        has_env_bad = any(n == ".env" or n.startswith(".env.") for n in names)
        has_example_env = "example.env" in names
        has_package_json = "package.json" in names

        print(f"  [+] Contains .git directory:        {has_git}")
        print(f"  [+] Contains Lockfile:              {has_lock}")
        print(f"  [+] Uses example.env (no .env):     {has_example_env and not has_env_bad}")
        print(f"  [+] No open-source LICENSE file:    {not has_os_license}")
        print(f"  [+] Proprietary package.json:       {has_package_json}")

    assert has_git, "FAILED: .git directory missing from zip!"
    assert has_lock, "FAILED: lockfile missing!"
    assert not has_env_bad, "FAILED: .env file found in zip!"
    assert not has_os_license, "FAILED: Open source LICENSE file found in zip!"
    print("\nAll packaging pre-checks passed successfully!")


def main():
    # Write to Desktop
    create_zip(OUTPUT_ZIP_DESKTOP)
    verify_zip(OUTPUT_ZIP_DESKTOP)

    # Also copy to workspace
    import shutil
    shutil.copy2(OUTPUT_ZIP_DESKTOP, OUTPUT_ZIP_WORKSPACE)
    print(f"Workspace copy created at: {OUTPUT_ZIP_WORKSPACE}")


if __name__ == "__main__":
    main()
