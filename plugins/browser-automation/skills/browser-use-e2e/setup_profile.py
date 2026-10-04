#!/usr/bin/env python3
"""
Setup persistent browser profile for 2FA-protected sites.

This script opens a browser where you can manually log in (including 2FA).
The authenticated session is saved to ~/.browser-use-profiles/<profile-name>
and can be reused in tests without re-authenticating.

Usage:
    python setup_profile.py --service github --profile-name github-2fa
    python setup_profile.py --url https://myapp.com/login --profile-name myapp-prod

Examples:
    # GitHub with 2FA
    python setup_profile.py --service github --profile-name github-2fa

    # Custom URL
    python setup_profile.py --url https://staging.example.com --profile-name staging

    # List existing profiles
    python setup_profile.py --list
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Known service login URLs
SERVICE_URLS = {
    "github": "https://github.com/login",
    "gitlab": "https://gitlab.com/users/sign_in",
    "google": "https://accounts.google.com",
    "gmail": "https://accounts.google.com",
    "bitbucket": "https://bitbucket.org/account/signin/",
    "azure": "https://portal.azure.com",
    "aws": "https://console.aws.amazon.com",
}

PROFILES_DIR = Path.home() / ".browser-use-profiles"


def list_profiles():
    """List all existing browser profiles."""
    if not PROFILES_DIR.exists():
        print("No profiles directory found.")
        return

    profiles = [p for p in PROFILES_DIR.iterdir() if p.is_dir()]
    if not profiles:
        print("No profiles found.")
        return

    print(f"Profiles in {PROFILES_DIR}:\n")
    for profile in sorted(profiles):
        print(f"  - {profile.name}")


async def setup_profile(url: str, profile_name: str):
    """Open browser for manual login, save session to profile."""
    try:
        # Optional native runtime, checked explicitly when this command is used.
        from browser_use import Browser  # ty: ignore[unresolved-import]
    except ImportError as exc:
        raise RuntimeError(
            "browser-use not installed. Run: uv add browser-use"
        ) from exc

    profile_dir = PROFILES_DIR / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nSetting up profile: {profile_name}")
    print(f"Profile directory: {profile_dir}")
    print(f"Login URL: {url}")
    print("\n" + "=" * 60)
    print("A browser window will open. Please:")
    print("  1. Log in to your account")
    print("  2. Complete any 2FA verification")
    print("  3. Return here and press Enter when done")
    print("=" * 60 + "\n")

    browser = Browser(
        headless=False,
        user_data_dir=str(profile_dir),
        profile_directory="Default",
    )

    try:
        await browser.start()
        await browser.new_page(url=url)
        input("Press Enter after completing login...")
    finally:
        await browser.stop()

    # A successful browser shutdown is not proof that anything was persisted.
    # Validate Chromium's on-disk profile, never print cookie/token contents.
    preferences = profile_dir / "Default" / "Preferences"
    try:
        persisted = json.loads(preferences.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"profile was not persisted: {preferences}") from exc
    if not isinstance(persisted, dict) or not persisted:
        raise RuntimeError(f"profile is empty or invalid: {preferences}")
    print(f"\nProfile saved to: {profile_dir}")
    print("Profile persistence verified; authentication must be verified by your test.")
    print("\nUsage in tests:")
    print(f"  browser = Browser(user_data_dir='{profile_dir}')")


def main():
    parser = argparse.ArgumentParser(
        description="Setup persistent browser profile for 2FA sites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--service",
        choices=list(SERVICE_URLS.keys()),
        help="Known service to set up (provides default URL)",
    )
    parser.add_argument(
        "--url",
        help="Custom login URL (overrides --service)",
    )
    parser.add_argument(
        "--profile-name",
        help="Name for the browser profile",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing profiles",
    )

    args = parser.parse_args()

    if args.list:
        list_profiles()
        return

    # Determine URL
    url = args.url
    if not url and args.service:
        url = SERVICE_URLS[args.service]
    if not url:
        parser.error("Either --service or --url is required")

    # Determine profile name
    profile_name = args.profile_name
    if not profile_name:
        if args.service:
            profile_name = f"{args.service}-profile"
        else:
            parser.error("--profile-name is required when using --url")

    try:
        asyncio.run(setup_profile(url, profile_name))
    except Exception as exc:  # noqa: BLE001 - CLI must report any browser failure
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
