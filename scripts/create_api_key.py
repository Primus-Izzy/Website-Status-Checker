#!/usr/bin/env python3
"""
Create API Key Script

Helper script to create API keys for the Website Status Checker API.
Requires admin authentication.

Usage:
    python scripts/create_api_key.py --name "My API Key" --admin-key YOUR_ADMIN_KEY

    Or with environment variable:
    export ADMIN_API_KEY=your-admin-key
    python scripts/create_api_key.py --name "My API Key"
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.auth.api_keys import create_api_key
from gui.config import get_settings


async def main():
    parser = argparse.ArgumentParser(
        description="Create an API key for the Website Status Checker API"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Descriptive name for the API key"
    )
    parser.add_argument(
        "--description",
        help="Optional description"
    )
    parser.add_argument(
        "--owner-email",
        help="Email of the key owner"
    )
    parser.add_argument(
        "--owner-name",
        help="Name of the key owner"
    )
    parser.add_argument(
        "--expires-days",
        type=int,
        help="Number of days until expiration (omit for no expiration)"
    )
    parser.add_argument(
        "--rate-limit-hour",
        type=int,
        default=1000,
        help="Maximum requests per hour (default: 1000)"
    )
    parser.add_argument(
        "--rate-limit-minute",
        type=int,
        default=100,
        help="Maximum requests per minute (default: 100)"
    )
    parser.add_argument(
        "--scopes",
        default="read,write",
        help="Comma-separated scopes (default: read,write)"
    )
    parser.add_argument(
        "--ip-whitelist",
        help="Comma-separated IP addresses to whitelist"
    )
    parser.add_argument(
        "--admin-key",
        help="Admin API key (or set ADMIN_API_KEY environment variable)"
    )

    args = parser.parse_args()

    # Get admin key
    admin_key = args.admin_key or os.getenv("ADMIN_API_KEY")
    if not admin_key:
        print("ERROR: Admin key required. Provide via --admin-key or ADMIN_API_KEY env variable")
        print("\nGenerate an admin key with:")
        print('  python -c "import secrets; print(secrets.token_hex(32))"')
        sys.exit(1)

    # Verify admin key matches settings
    settings = get_settings()
    if admin_key != settings.admin_api_key and admin_key != settings.secret_key:
        print("ERROR: Invalid admin key")
        sys.exit(1)

    print(f"Creating API key: {args.name}")
    print(f"  Rate limits: {args.rate_limit_per_minute}/min, {args.rate_limit_per_hour}/hour")
    print(f"  Scopes: {args.scopes}")
    if args.expires_days:
        print(f"  Expires in: {args.expires_days} days")
    print()

    try:
        # Create the API key
        raw_key, api_key_model = await create_api_key(
            name=args.name,
            description=args.description,
            owner_email=args.owner_email,
            owner_name=args.owner_name,
            expires_days=args.expires_days,
            rate_limit_per_hour=args.rate_limit_hour,
            rate_limit_per_minute=args.rate_limit_minute,
            scopes=args.scopes,
            ip_whitelist=args.ip_whitelist,
        )

        print("✅ API Key Created Successfully!")
        print()
        print("=" * 70)
        print(f"API Key: {raw_key}")
        print("=" * 70)
        print()
        print("⚠️  IMPORTANT: Save this key securely!")
        print("   This is the only time you will see the full key.")
        print()
        print("Key Information:")
        print(f"  ID: {api_key_model.id}")
        print(f"  Name: {api_key_model.name}")
        print(f"  Prefix: {api_key_model.key_prefix}")
        print(f"  Created: {api_key_model.created_at}")
        if api_key_model.expires_at:
            print(f"  Expires: {api_key_model.expires_at}")
        print()
        print("Usage:")
        print(f'  curl -H "X-API-Key: {raw_key}" https://your-domain.com/api/...')
        print()

    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
