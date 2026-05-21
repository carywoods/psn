"""
API Key Authentication and Rate Limiting
"""
import sqlite3
import secrets
import logging
from datetime import datetime
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader

from .config import API_KEYS_DB_PATH, RATE_LIMITS

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def init_api_keys_db():
    """Initialize the API keys database"""
    API_KEYS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(API_KEYS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            tier TEXT NOT NULL CHECK (tier IN ('free', 'pro', 'enterprise')),
            created_at TEXT NOT NULL,
            rate_limit_monthly INTEGER NOT NULL,
            calls_this_month INTEGER NOT NULL DEFAULT 0,
            last_reset TEXT NOT NULL,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logger.info(f"API keys database initialized at {API_KEYS_DB_PATH}")


def create_api_key(tier: str, description: str = None) -> str:
    """Create a new API key"""
    if tier not in RATE_LIMITS:
        raise ValueError(f"Invalid tier: {tier}. Must be one of {list(RATE_LIMITS.keys())}")

    key = f"psn_{secrets.token_urlsafe(32)}"
    now = datetime.utcnow().isoformat()
    rate_limit = RATE_LIMITS[tier]

    conn = sqlite3.connect(API_KEYS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO api_keys (key, tier, created_at, rate_limit_monthly, calls_this_month, last_reset, description) VALUES (?, ?, ?, ?, 0, ?, ?)",
        (key, tier, now, rate_limit, now, description)
    )
    conn.commit()
    conn.close()

    logger.info(f"Created new {tier} API key: ...{key[-8:]}")
    return key


def validate_api_key(key: str) -> Optional[dict]:
    """Validate an API key and return its info"""
    conn = sqlite3.connect(API_KEYS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT tier, rate_limit_monthly, calls_this_month, last_reset FROM api_keys WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "tier": row[0],
        "rate_limit_monthly": row[1],
        "calls_this_month": row[2],
        "last_reset": row[3]
    }


def increment_call_count(key: str):
    """Increment the call count for an API key"""
    conn = sqlite3.connect(API_KEYS_DB_PATH)
    cursor = conn.cursor()

    # Check if we need to reset the monthly counter
    cursor.execute("SELECT last_reset FROM api_keys WHERE key = ?", (key,))
    row = cursor.fetchone()
    if row:
        last_reset = datetime.fromisoformat(row[0])
        now = datetime.utcnow()
        # Reset if we're in a new month
        if now.month != last_reset.month or now.year != last_reset.year:
            cursor.execute(
                "UPDATE api_keys SET calls_this_month = 1, last_reset = ? WHERE key = ?",
                (now.isoformat(), key)
            )
        else:
            cursor.execute(
                "UPDATE api_keys SET calls_this_month = calls_this_month + 1 WHERE key = ?",
                (key,)
            )

    conn.commit()
    conn.close()


def list_api_keys() -> list[dict]:
    """List all API keys"""
    conn = sqlite3.connect(API_KEYS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, tier, created_at, rate_limit_monthly, calls_this_month, description FROM api_keys")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "key_suffix": row[0][-8:],
            "tier": row[1],
            "created_at": row[2],
            "rate_limit_monthly": row[3],
            "calls_this_month": row[4],
            "description": row[5]
        }
        for row in rows
    ]


def revoke_api_key(key_suffix: str) -> bool:
    """Revoke an API key by its last 8 characters"""
    conn = sqlite3.connect(API_KEYS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM api_keys WHERE key LIKE ?", (f"%{key_suffix}",))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def reset_call_counts():
    """Reset all call counts (for manual reset)"""
    conn = sqlite3.connect(API_KEYS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE api_keys SET calls_this_month = 0, last_reset = ?", (datetime.utcnow().isoformat(),))
    conn.commit()
    conn.close()


async def get_api_key(api_key: str = Depends(api_key_header)) -> dict:
    """FastAPI dependency for API key validation"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "MISSING_API_KEY", "message": "X-API-Key header is required"}}
        )

    key_info = validate_api_key(api_key)
    if not key_info:
        logger.warning(f"Invalid API key attempted: ...{api_key[-8:] if len(api_key) > 8 else 'SHORT'}")
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "INVALID_API_KEY", "message": "Invalid API key"}}
        )

    # Check rate limit
    if key_info["calls_this_month"] >= key_info["rate_limit_monthly"]:
        remaining = key_info["rate_limit_monthly"] - key_info["calls_this_month"]
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Monthly rate limit exceeded",
                    "details": {
                        "tier": key_info["tier"],
                        "limit": key_info["rate_limit_monthly"],
                        "used": key_info["calls_this_month"],
                        "remaining": max(0, remaining)
                    }
                }
            },
            headers={"Retry-After": "2592000"}  # 30 days in seconds
        )

    # Increment call count
    increment_call_count(api_key)

    return key_info
