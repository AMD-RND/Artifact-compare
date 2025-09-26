#!/usr/bin/env python3
"""
fetch_latest_commits.py

Download `latest_commits.txt` from Artifactory build folders for specified builds and platforms.

Usage examples:
  # Use token in ARTIFACTORY_TOKEN (recommended)
  export ARTIFACTORY_TOKEN="..." 
  python3 scripts/fetch_latest_commits.py --base-url "https://xcoartifactory.xilinx.com/native/vai-rt-ipu-prod-local/com/amd/onnx-rt/stx/cp_dev" --builds 3025 3026 --platforms windows linux arm --out data/builds

  # Or provide basic auth
  python3 scripts/fetch_latest_commits.py --base-url "https://..." --builds 3025 3026 --platforms windows linux --user myuser --password "mypw" --out data/builds

Description:
  For each build in --builds and each platform in --platforms, the script will attempt to download:
    {base_url}/{build}/{platform}/latest_commits.txt
  Saved local path: {out}/{build}/{platform}/latest_commits.txt
  Also creates a meta.json with retrieval timestamp and source URL.

Notes:
  - Prefer setting ARTIFACTORY_TOKEN env var. If not set, supply --user and --password for Basic auth.
  - Retries on transient failures (3 attempts with exponential backoff).
  - Exits with non-zero code on fatal errors.
"""

import argparse
import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    import requests
except Exception:
    print("Missing dependency 'requests'. Install with: pip install requests", file=sys.stderr)
    raise

DEFAULT_RETRIES = 3
BACKOFF_FACTOR = 1.5
TIMEOUT = 30  # seconds

def build_target_url(base_url: str, build: str, platform: str) -> str:
    base = base_url.rstrip('/')
    return f"{base}/{build}/{platform}/latest_commits.txt"

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def write_meta(path: Path, build: str, platform: str, source_url: str):
    meta = {
        "build": build,
        "platform": platform,
        "fetched_at": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "source_url": source_url
    }
    meta_path = path.parent / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

def fetch_url(session, url, auth=None, headers=None, retries=DEFAULT_RETRIES, timeout=TIMEOUT):
    attempt = 0
    while attempt < retries:
        try:
            resp = session.get(url, auth=auth, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp.text, resp.status_code, resp.headers
            elif resp.status_code in (401,403):
                # Auth issues -> fatal, return so caller can stop or report clearly
                return None, resp.status_code, resp.headers
            else:
                # retry for 5xx or intermittent errors
                attempt += 1
                sleep = BACKOFF_FACTOR ** attempt
                time.sleep(sleep)
        except requests.exceptions.RequestException:
            attempt += 1
            sleep = BACKOFF_FACTOR ** attempt
            time.sleep(sleep)
    return None, None, None

def main():
    parser = argparse.ArgumentParser(description="Download latest_commits.txt for builds/platforms from Artifactory")
    parser.add_argument("--base-url", required=True, help="Base Artifactory URL, e.g. https://xcoartifactory.xilinx.com/native/vai-rt-ipu-prod-local/com/amd/onnx-rt/stx/cp_dev")
    parser.add_argument("--builds", required=True, nargs="+", help="Build IDs to fetch, e.g. 3025 3026")
    parser.add_argument("--platforms", required=True, nargs="+", help="Platforms to fetch, e.g. windows linux arm")
    parser.add_argument("--out", default="data/builds", help="Output root directory to save files")
    parser.add_argument("--user", help="Username for basic auth (if not using token)")
    parser.add_argument("--password", help="Password for basic auth (if not using token)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Number of retries on transient failures")
    args = parser.parse_args()

    token = os.environ.get("ARTIFACTORY_TOKEN")
    use_token = bool(token)
    if not use_token and (not args.user or not args.password):
        print("Warning: No ARTIFACTORY_TOKEN found. Provide --user/--password for Basic auth or set ARTIFACTORY_TOKEN env var.", file=sys.stderr)

    session = requests.Session()

    headers = {}
    auth = None
    if use_token:
        headers["Authorization"] = f"Bearer {token}"
    elif args.user and args.password:
        auth = (args.user, args.password)

    base_url = args.base_url.rstrip("/")
    out_root = Path(args.out)

    errors = []
    success_count = 0

    for build in args.builds:
        for plat in args.platforms:
            target_url = build_target_url(base_url, build, plat)
            local_path = out_root / str(build) / plat / "latest_commits.txt"
            print(f"Fetching: {target_url} -> {local_path}")
            content, status, resp_headers = fetch_url(session, target_url, auth=auth, headers=headers, retries=args.retries)
            if content is None:
                if status in (401,403):
                    msg = f"AUTH ERROR {status} fetching {target_url}"
                    print(msg, file=sys.stderr)
                    errors.append({"build": build, "platform": plat, "url": target_url, "error": msg})
                else:
                    msg = f"FAILED to fetch {target_url} after {args.retries} attempts"
                    print(msg, file=sys.stderr)
                    errors.append({"build": build, "platform": plat, "url": target_url, "error": msg})
                continue
            # successful
            write_file(local_path, content)
            write_meta(local_path, build, plat, target_url)
            print(f"Saved {local_path} ({len(content)} bytes)")
            success_count += 1

    print(f"\nCompleted. Successful files: {success_count}. Errors: {len(errors)}")
    if errors:
        err_path = out_root / "fetch_errors.json"
        err_path.write_text(json.dumps(errors, indent=2), encoding="utf-8")
        print(f"Errors written to {err_path}", file=sys.stderr)
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
