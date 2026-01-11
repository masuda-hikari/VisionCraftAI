#!/usr/bin/env python3
"""
Quick Deploy Script

VisionCraftAI deployment guide script.
Checks and resolves blockers one by one before deployment.

Usage:
    python scripts/quick_deploy.py

Manual actions required:
1. Make GitHub repository public
2. Set up Google Cloud credentials
3. Set up Stripe production API key
"""

import os
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def print_header(title: str) -> None:
    """Print header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_step(step: int, title: str) -> None:
    """Print step"""
    print(f"\n[Step {step}] {title}")
    print("-" * 40)


def check_github_public() -> bool:
    """Check if GitHub repository is public"""
    import urllib.request
    import urllib.error

    url = "https://api.github.com/repos/masuda-hikari/VisionCraftAI"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.status == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


def check_gcloud_auth() -> bool:
    """Check gcloud authentication status"""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "list", "--format=value(account)"],
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())
    except FileNotFoundError:
        return False


def check_env_file() -> dict:
    """Check environment file status"""
    env_path = Path(__file__).parent.parent / ".env"
    result = {
        "exists": env_path.exists(),
        "google_credentials": False,
        "stripe_key": False,
    }
    if env_path.exists():
        content = env_path.read_text()
        result["google_credentials"] = "GOOGLE_APPLICATION_CREDENTIALS" in content
        result["stripe_key"] = "STRIPE_API_KEY" in content and "sk_live" in content
    return result


def main():
    """Main process"""
    print_header("VisionCraftAI Quick Deploy")
    print("This script checks deployment requirements and")
    print("resolves blockers one by one.\n")

    blockers = []
    ready_items = []

    # Step 1: Check GitHub repository
    print_step(1, "GitHub Repository Visibility Check")
    if check_github_public():
        print("[OK] Repository is public")
        ready_items.append("GitHub Repository Public")
    else:
        print("[NG] Repository is private or inaccessible")
        print("\n[Action Required]:")
        print("   1. Go to https://github.com/masuda-hikari/VisionCraftAI/settings")
        print("   2. Scroll to 'Danger Zone' section")
        print("   3. Click 'Change repository visibility'")
        print("   4. Select 'Make public' and confirm")
        blockers.append("GitHub Repository Public")

    # Step 2: Check gcloud authentication
    print_step(2, "Google Cloud Authentication Check")
    if check_gcloud_auth():
        print("[OK] gcloud is authenticated")
        ready_items.append("Google Cloud Auth")
    else:
        print("[NG] gcloud is not authenticated")
        print("\n[Action Required]:")
        print("   1. gcloud auth login")
        print("   2. python scripts/setup_gcloud.py --project YOUR_PROJECT_ID")
        blockers.append("Google Cloud Auth")

    # Step 3: Check environment variables
    print_step(3, "Environment File Check")
    env_status = check_env_file()
    if env_status["exists"]:
        print("[OK] .env file exists")
    else:
        print("[WARN] .env file does not exist (copy from .env.example)")
        blockers.append(".env file creation")

    if env_status["stripe_key"]:
        print("[OK] Stripe production API key is configured")
        ready_items.append("Stripe API Config")
    else:
        print("[NG] Stripe production API key is not configured")
        print("\n[Action Required]:")
        print("   1. Go to https://dashboard.stripe.com/apikeys")
        print("   2. Copy production API key (sk_live_xxx)")
        print("   3. Add STRIPE_API_KEY=sk_live_xxx to .env file")
        blockers.append("Stripe API Config")

    # Step 4: Check tests
    print_step(4, "Test Status Check")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=120,
        )
        if result.returncode == 0:
            print("[OK] All tests passed")
            for line in result.stdout.split("\n"):
                if "passed" in line:
                    print(f"   {line.strip()}")
            ready_items.append("Tests Passed")
        else:
            print("[NG] Some tests failed")
            blockers.append("Test Failures")
    except subprocess.TimeoutExpired:
        print("[WARN] Test execution timed out")
    except Exception as e:
        print(f"[WARN] Test execution error: {e}")

    # Summary
    print_header("Deployment Readiness Summary")
    print(f"[READY] {len(ready_items)} items")
    for item in ready_items:
        print(f"   - {item}")

    print(f"\n[BLOCKED] {len(blockers)} items")
    for item in blockers:
        print(f"   - {item}")

    if not blockers:
        print("\n[SUCCESS] All requirements met!")
        print("Run the following command to deploy:")
        print("\n   python scripts/deploy_cloudrun.py --project YOUR_PROJECT_ID")
    else:
        print("\n[ACTION] Resolve blockers and run this script again.")
        print("\n[DEMO MODE] Quick deploy without credentials:")
        print("   1. Go to Render.com: https://render.com")
        print("   2. Click 'New +' -> 'Web Service'")
        print("   3. Connect GitHub repository (must be Public)")
        print("   4. render.yaml will be auto-detected, DEMO_MODE=true")

    return len(blockers) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
