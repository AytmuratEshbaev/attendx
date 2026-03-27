"""
AttendX Deployment Verification Script.

Runs post-deployment checks to confirm all critical services are operational.

Usage:
    python -m scripts.verify_deployment --base-url https://your-domain.com
    python -m scripts.verify_deployment --base-url http://localhost:8000
"""

import argparse
import json
import sys
import urllib.request
from urllib.error import URLError


def _get(url: str, headers: dict | None = None, timeout: int = 10) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except URLError as exc:
        return {"_error": str(exc)}


def check_health(base_url: str) -> bool:
    print("==> Checking /health ...")
    data = _get(f"{base_url}/health")
    if "_error" in data:
        print(f"    FAIL: {data['_error']}")
        return False
    status = data.get("status", "unknown")
    if status in ("ok", "healthy"):
        print(f"    OK — status: {status}")
        return True
    print(f"    WARN — status: {status}")
    return status != "error"


def check_detailed_health(base_url: str, token: str) -> bool:
    print("==> Checking /health/detailed ...")
    data = _get(
        f"{base_url}/health/detailed",
        headers={"Authorization": f"Bearer {token}"},
    )
    if "_error" in data:
        print(f"    FAIL: {data['_error']}")
        return False
    checks = data.get("checks", {})
    all_ok = True
    for name, result in checks.items():
        status = result if isinstance(result, str) else result.get("status", "unknown")
        icon = "✅" if status in ("ok", "connected", True) else "⚠️ "
        print(f"    {icon} {name}: {status}")
        if status in ("error", False):
            all_ok = False
    return all_ok


def check_openapi(base_url: str) -> bool:
    print("==> Checking /openapi.json ...")
    data = _get(f"{base_url}/openapi.json")
    if "_error" in data:
        print(f"    FAIL: {data['_error']}")
        return False
    title = data.get("info", {}).get("title", "unknown")
    version = data.get("info", {}).get("version", "unknown")
    paths = len(data.get("paths", {}))
    print(f"    OK — {title} v{version}, {paths} routes")
    return True


def check_login(base_url: str, username: str, password: str) -> str | None:
    print(f"==> Testing login as '{username}' ...")
    payload = f"username={username}&password={password}".encode()
    req = urllib.request.Request(
        f"{base_url}/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            token = data.get("access_token")
            if token:
                print(f"    OK — token obtained (expires in {data.get('expires_in', '?')}s)")
                return token
            print("    FAIL — no access_token in response")
            return None
    except URLError as exc:
        print(f"    FAIL: {exc}")
        return None


def check_security_headers(base_url: str) -> bool:
    print("==> Checking security headers ...")
    req = urllib.request.Request(f"{base_url}/health")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            headers = dict(resp.headers)
            required = {
                "x-content-type-options": "nosniff",
                "x-frame-options": "DENY",
            }
            ok = True
            for header, expected in required.items():
                actual = headers.get(header, "").lower()
                if expected.lower() in actual:
                    print(f"    ✅ {header}: {actual}")
                else:
                    print(f"    ⚠️  {header} missing or wrong (got: '{actual}')")
                    ok = False
            return ok
    except URLError as exc:
        print(f"    FAIL: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify AttendX deployment")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--username", default="admin", help="Admin username for login test")
    parser.add_argument("--password", default="AttendX@2025", help="Admin password for login test")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    print(f"\nAttendX Deployment Verification — {base_url}\n{'=' * 60}")

    results: list[bool] = []

    results.append(check_health(base_url))
    results.append(check_openapi(base_url))
    results.append(check_security_headers(base_url))

    token = check_login(base_url, args.username, args.password)
    results.append(token is not None)

    if token:
        results.append(check_detailed_health(base_url, token))

    print(f"\n{'=' * 60}")
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"✅  All {total} checks passed — deployment looks healthy!")
        sys.exit(0)
    else:
        print(f"⚠️  {passed}/{total} checks passed — review warnings above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
