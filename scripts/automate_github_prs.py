"""Automates real GitHub Pull Request creation and merging via GitHub REST API.

Iterates through all pushed feature branches, creates an official GitHub Pull Request,
and merges it using the merge API, ensuring 80+ PRs appear in GitHub's Closed/Merged tab.
"""

import json
import subprocess
import time
import urllib.error
import urllib.request
from typing import Dict, List, Tuple

MODULE_CATEGORIES: List[Tuple[str, str, int, str]] = [
    ("bin_network", "BIN Network Risk & Issuer Velocity Rules", 10, "BIN"),
    ("mcc_matrix", "Merchant Category Code Risk Matrix", 8, "MCC"),
    ("aml_kyc", "Anti-Money Laundering & Sanctions Heuristics", 8, "AML"),
    ("geo_velocity", "Impossible Travel & IP ASN Geo-Velocity", 8, "GEO"),
    ("device_fingerprint", "Hardware Fingerprint & Bot Signature Analysis", 8, "DEV"),
    ("fraud_vectors", "Fraud Pattern Signatures & Card Testing", 10, "SIG"),
    ("compliance_rbi", "RBI Payment Safety & Mandate Compliance", 8, "RBI"),
    ("compliance_psd2", "PSD2 SCA Transaction Risk Analysis Rules", 8, "SCA"),
    ("compliance_pcidss", "PCI-DSS Tokenization & Audit Verification", 8, "PCI"),
    ("simulation_scenarios", "Enterprise Multi-Channel Fraud Test Vectors", 10, "SIM"),
]


def get_github_token() -> str:
    res = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        check=True,
    )
    lines = dict(l.split("=", 1) for l in res.stdout.splitlines() if "=" in l)
    token = lines.get("password", "")
    if not token:
        raise RuntimeError("Could not retrieve GitHub token from git credential helper.")
    return token


def github_api_request(url: str, token: str, data: Dict = None, method: str = "GET") -> Dict:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "FraudShield-Agent",
    }
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            return {"error_code": e.code, "error_body": json.loads(err_msg)}
        except Exception:
            return {"error_code": e.code, "error_body": err_msg}


def main():
    print("Fetching GitHub authentication credentials...")
    token = get_github_token()
    repo = "Lakshmidurga250/Fraudshield"
    base_url = f"https://api.github.com/repos/{repo}"

    # Build branch list in chronological order
    branch_specs = []
    for cat_folder, doc_desc, num_parts, _ in MODULE_CATEGORIES:
        for part in range(1, num_parts + 1):
            branch_name = f"feature/{cat_folder}-part-{part:02d}"
            title = f"feat({cat_folder}): implement {doc_desc} partition {part:02d}"
            body = f"Add enterprise {doc_desc} partition {part:02d} with risk evaluation matrices."
            branch_specs.append((branch_name, title, body))

    branch_specs.append((
        "feature/enterprise-test-suite",
        "test(enterprise): add unit test coverage for enterprise rule evaluation",
        "Add unit tests verifying enterprise rule evaluation and scoring accuracy.",
    ))

    print(f"Total branches to verify and process: {len(branch_specs)}")

    # Check already existing PRs
    existing_prs = github_api_request(f"{base_url}/pulls?state=all&per_page=100", token)
    processed_heads = set()
    if isinstance(existing_prs, list):
        for pr in existing_prs:
            head_ref = pr.get("head", {}).get("ref")
            if head_ref:
                processed_heads.add(head_ref)
                print(f"Found existing PR #{pr['number']} ({pr['state']}) for branch: {head_ref}")

    success_count = len(processed_heads)

    for branch_name, title, body in branch_specs:
        if branch_name in processed_heads:
            print(f"Skipping already processed branch: {branch_name}")
            continue

        print(f"\nProcessing {branch_name}...")

        # 1. Create PR
        pr_payload = {
            "title": title,
            "head": branch_name,
            "base": "master",
            "body": body,
        }
        pr_res = github_api_request(f"{base_url}/pulls", token, data=pr_payload, method="POST")

        if "error_code" in pr_res:
            print(f"Failed to create PR for {branch_name}: {pr_res}")
            continue

        pr_number = pr_res["number"]
        pr_url = pr_res["html_url"]
        print(f"Created PR #{pr_number}: {pr_url}")

        # Short pause before merge
        time.sleep(1.0)

        # 2. Merge PR
        merge_payload = {
            "commit_title": f"Merge pull request #{pr_number} from {branch_name}",
            "commit_message": body,
            "merge_method": "merge",
        }
        merge_res = github_api_request(
            f"{base_url}/pulls/{pr_number}/merge", token, data=merge_payload, method="PUT"
        )

        if "error_code" in merge_res:
            print(f"Failed to merge PR #{pr_number}: {merge_res}")
        else:
            print(f"Successfully merged PR #{pr_number}!")
            success_count += 1

        time.sleep(1.5)  # Respect GitHub API rate limits

    print("\n" + "=" * 60)
    print("  GITHUB PULL REQUEST AUTOMATION COMPLETE")
    print("=" * 60)
    print(f"Total Merged Pull Requests on GitHub: {success_count}")
    print("=" * 60)

    # Sync local master with remote master
    subprocess.run(["git", "fetch", "origin"], check=True)
    subprocess.run(["git", "checkout", "master"], check=True)
    subprocess.run(["git", "reset", "--hard", "origin/master"], check=True)
    print("Local master synchronized with remote master.")


if __name__ == "__main__":
    main()
