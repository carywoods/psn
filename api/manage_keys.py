#!/usr/bin/env python3
"""
API Key Management CLI

Usage:
    python api/manage_keys.py create --tier pro --description "My API key"
    python api/manage_keys.py list
    python api/manage_keys.py revoke --key-suffix xxxxxxxx
    python api/manage_keys.py reset-counts
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.auth import (
    init_api_keys_db, create_api_key, list_api_keys,
    revoke_api_key, reset_call_counts
)


def cmd_create(args):
    """Create a new API key"""
    init_api_keys_db()
    key = create_api_key(args.tier, args.description)
    print(f"\nAPI Key created successfully!")
    print(f"Tier: {args.tier}")
    print(f"Key: {key}")
    print(f"\nIMPORTANT: Save this key securely. It cannot be retrieved later.")
    print(f"Use with header: X-API-Key: {key}")


def cmd_list(args):
    """List all API keys"""
    init_api_keys_db()
    keys = list_api_keys()

    if not keys:
        print("No API keys found.")
        return

    print(f"\n{'Suffix':<12} {'Tier':<12} {'Used/Limit':<15} {'Description'}")
    print("-" * 60)
    for k in keys:
        usage = f"{k['calls_this_month']}/{k['rate_limit_monthly']}"
        desc = k['description'] or '-'
        print(f"...{k['key_suffix']:<8} {k['tier']:<12} {usage:<15} {desc}")
    print()


def cmd_revoke(args):
    """Revoke an API key"""
    init_api_keys_db()
    if revoke_api_key(args.key_suffix):
        print(f"API key ...{args.key_suffix} revoked successfully.")
    else:
        print(f"No API key found with suffix: {args.key_suffix}")
        sys.exit(1)


def cmd_reset_counts(args):
    """Reset all call counts"""
    init_api_keys_db()
    reset_call_counts()
    print("All call counts have been reset.")


def main():
    parser = argparse.ArgumentParser(description="PSN API Key Management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument(
        "--tier", required=True, choices=["free", "pro", "enterprise"],
        help="API tier (determines rate limit)"
    )
    create_parser.add_argument(
        "--description", "-d", default=None,
        help="Optional description for the key"
    )
    create_parser.set_defaults(func=cmd_create)

    # list command
    list_parser = subparsers.add_parser("list", help="List all API keys")
    list_parser.set_defaults(func=cmd_list)

    # revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke_parser.add_argument(
        "--key-suffix", required=True,
        help="Last 8 characters of the API key to revoke"
    )
    revoke_parser.set_defaults(func=cmd_revoke)

    # reset-counts command
    reset_parser = subparsers.add_parser("reset-counts", help="Reset all call counts")
    reset_parser.set_defaults(func=cmd_reset_counts)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
