"""
rate_limit.py — Lightweight daily rate limiting via Upstash Redis (REST).

Two ceilings protect the API budget without accounts or payments:
  - per-identity daily limit (soft; curbs casual repeat use)
  - global daily limit (hard wallet cap across ALL users)

Config (env):
  UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN   # from the Upstash console
  RL_PER_USER_DAILY   (default 10)
  RL_GLOBAL_DAILY     (default 200)

If Upstash is not configured or unreachable, the limiter FAILS OPEN (allows the
request) so the app keeps working; a warning is logged so you know protection
is off. The global cap is your real backstop; the per-user cap is best-effort
because a determined user can rotate sessions/IPs.
"""

import os
from datetime import datetime, timezone

PER_USER_DAILY = int(os.getenv("RL_PER_USER_DAILY", "10"))
GLOBAL_DAILY = int(os.getenv("RL_GLOBAL_DAILY", "200"))
_DAY_SECONDS = 86400


def _redis():
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return None
    try:
        from upstash_redis import Redis
        return Redis(url=url, token=token)
    except Exception as e:
        print(f"[rate_limit] Redis init failed, failing open: {e}")
        return None


def _today():
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def check_and_increment(identity):
    """Return (allowed: bool, message: str).

    Counters are only incremented when the request is allowed, so a blocked
    attempt does not consume quota.
    """
    r = _redis()
    if r is None:
        print("[rate_limit] Upstash not configured - failing open (no limit enforced)")
        return True, ""

    day = _today()
    gkey = f"rl:gen:global:{day}"
    ukey = f"rl:gen:user:{day}:{identity}"

    try:
        gcount = int(r.get(gkey) or 0)
        ucount = int(r.get(ukey) or 0)
    except Exception as e:
        print(f"[rate_limit] read failed, failing open: {e}")
        return True, ""

    if gcount >= GLOBAL_DAILY:
        return False, "This app has hit its daily generation cap. Please try again tomorrow."
    if ucount >= PER_USER_DAILY:
        return False, f"You've reached the daily limit of {PER_USER_DAILY} generations. Please try again tomorrow."

    try:
        new_u = r.incr(ukey)
        if new_u == 1:
            r.expire(ukey, _DAY_SECONDS)
        new_g = r.incr(gkey)
        if new_g == 1:
            r.expire(gkey, _DAY_SECONDS)
    except Exception as e:
        print(f"[rate_limit] increment failed, failing open: {e}")
        return True, ""

    remaining = max(0, PER_USER_DAILY - new_u)
    return True, f"{remaining} of {PER_USER_DAILY} generations left today."
