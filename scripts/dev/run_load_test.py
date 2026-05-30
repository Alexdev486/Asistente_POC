#!/usr/bin/env python3
"""Light load test for the Asistente_POC API.

Simulates multiple concurrent sessions exercising the VIN → FAQ → Feedback flow.
Verifies connection pool stability and response times.

Usage:
    python scripts/dev/run_load_test.py [--base-url URL] [--concurrency N] [--sessions N]

Requires:
    httpx  (already in requirements.txt)

Example:
    # Quick smoke test (5 sessions, 3 concurrent):
    python scripts/dev/run_load_test.py --concurrency 3 --sessions 5

    # Moderate load (20 sessions, 5 concurrent):
    python scripts/dev/run_load_test.py --concurrency 5 --sessions 20
"""

import argparse
import json
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import httpx

BASE_URL = "http://localhost:8000/api/v1"
VALID_VINS = [
    "AK550-POC-0001",
    "AK550-POC-0002",
    "XCITING-POC-0001",
]
TIMEOUT = 30.0


def run_session(client: httpx.Client, vin: str, session_num: int) -> dict:
    """Execute a single session: Start → VIN → FAQ → Feedback.

    Returns timing and status info.
    """
    timings = {}
    errors = []
    session_id: str | None = None

    try:
        # ── Start session ──────────────────────────────────────
        t0 = time.monotonic()
        r = client.post("/session/start", json={})
        timings["start_ms"] = round((time.monotonic() - t0) * 1000, 1)
        if r.status_code != 200:
            errors.append(f"start: HTTP {r.status_code}")
        else:
            session_id = r.json().get("session_id")

        if session_id is None:
            return {
                "session_num": session_num,
                "success": False,
                "errors": errors or ["no_session_id"],
                "timings": timings,
                "steps": 0,
            }

        # ── VIN lookup ─────────────────────────────────────────
        t0 = time.monotonic()
        r = client.post(
            "/session/message",
            json={"session_id": session_id, "message": vin},
        )
        timings["vin_ms"] = round((time.monotonic() - t0) * 1000, 1)
        if r.status_code != 200:
            errors.append(f"vin: HTTP {r.status_code}")
        else:
            data = r.json()
            if data.get("state", {}).get("vin") != vin:
                errors.append(f"vin_mismatch: got {data.get('state', {}).get('vin')}")

        # ── FAQ ─────────────────────────────────────────────────
        t0 = time.monotonic()
        r = client.post(
            "/session/message",
            json={"session_id": session_id, "message": "Consultas frecuentes"},
        )
        timings["faq_ms"] = round((time.monotonic() - t0) * 1000, 1)
        if r.status_code != 200:
            errors.append(f"faq: HTTP {r.status_code}")

        # ── FAQ question ────────────────────────────────────────
        t0 = time.monotonic()
        r = client.post(
            "/session/message",
            json={
                "session_id": session_id,
                "message": "Por que se enciende el testigo CELP?",
            },
        )
        timings["faq_q_ms"] = round((time.monotonic() - t0) * 1000, 1)
        if r.status_code != 200:
            errors.append(f"faq_q: HTTP {r.status_code}")

        # ── Feedback ────────────────────────────────────────────
        t0 = time.monotonic()
        r = client.post(
            f"/session/{session_id}/feedback",
            json={"useful": True, "comment": f"Load test session {session_num}"},
        )
        timings["feedback_ms"] = round((time.monotonic() - t0) * 1000, 1)
        if r.status_code != 200:
            errors.append(f"feedback: HTTP {r.status_code}")

        # ── Get session (verify completed) ──────────────────────
        t0 = time.monotonic()
        r = client.get(f"/session/{session_id}")
        timings["get_ms"] = round((time.monotonic() - t0) * 1000, 1)
        if r.status_code != 200:
            errors.append(f"get: HTTP {r.status_code}")

        total_ms = round(sum(timings.values()), 1)

        return {
            "session_num": session_num,
            "session_id": session_id,
            "success": len(errors) == 0,
            "errors": errors,
            "timings": timings,
            "total_ms": total_ms,
            "steps": 4,
        }

    except httpx.HTTPError as exc:
        return {
            "session_num": session_num,
            "success": False,
            "errors": [f"httpx: {exc.__class__.__name__}: {exc}"],
            "timings": timings,
            "steps": 0,
        }
    except Exception as exc:
        return {
            "session_num": session_num,
            "success": False,
            "errors": [f"unexpected: {exc.__class__.__name__}: {exc}"],
            "timings": timings,
            "steps": 0,
        }


def print_summary(results: list[dict], total_duration: float) -> None:
    """Print a human-readable summary of load test results."""
    total = len(results)
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    successful_timings = [r.get("total_ms", 0) for r in successes]
    all_timings = [r.get("total_ms", 0) for r in results if "total_ms" in r]

    print()
    print("=" * 60)
    print("  LOAD TEST SUMMARY")
    print("=" * 60)
    print(f"  Total wall time:       {total_duration:.2f}s")
    print(f"  Sessions attempted:    {total}")
    print(f"  Sessions successful:   {len(successes)}")
    print(f"  Sessions failed:       {len(failures)}")
    print()

    if successful_timings:
        avg = sum(successful_timings) / len(successful_timings)
        print(f"  Avg session time:     {avg:.1f}ms")
        print(f"  Min session time:     {min(successful_timings):.1f}ms")
        print(f"  Max session time:     {max(successful_timings):.1f}ms")
        print(f"  Median session time:  {sorted(successful_timings)[len(successful_timings)//2]:.1f}ms")
    print()

    if successes:
        faq_times = [r["timings"].get("faq_ms", 0) for r in successes]
        vin_times = [r["timings"].get("vin_ms", 0) for r in successes]
        feedback_times = [r["timings"].get("feedback_ms", 0) for r in successes]
        print(f"  Avg VIN lookup:       {sum(vin_times)/len(vin_times):.1f}ms")
        print(f"  Avg FAQ match:        {sum(faq_times)/len(faq_times):.1f}ms")
        print(f"  Avg Feedback save:    {sum(feedback_times)/len(feedback_times):.1f}ms")
    print()

    if failures:
        print("  FAILURES:")
        for f in failures[:10]:  # show first 10
            session = f["session_num"]
            errs = "; ".join(f.get("errors", ["unknown"]))
            print(f"    Session {session}: {errs}")
        if len(failures) > 10:
            print(f"    ... and {len(failures) - 10} more")
    print()

    # Metrics check
    try:
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
            r = c.get("/metrics/summary")
            if r.status_code == 200:
                metrics = r.json()
                print(f"  Metrics — total_sessions: {metrics['total_sessions']}")
                print(f"  Metrics — completed:      {metrics['completed_sessions']}")
                print(f"  Metrics — faq_usage:      {metrics['faq_usage']}")
                print(f"  Metrics — positive_fb:    {metrics['positive_feedback']}")
                print(f"  Metrics — negative_fb:    {metrics['negative_feedback']}")
    except Exception as exc:
        print(f"  Metrics unavailable: {exc}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Light load test for Asistente_POC API")
    parser.add_argument("--base-url", default=BASE_URL, help="API base URL (default: %(default)s)")
    parser.add_argument("--concurrency", type=int, default=3, help="Max concurrent sessions (default: %(default)s)")
    parser.add_argument("--sessions", type=int, default=5, help="Total sessions to run (default: %(default)s)")
    args = parser.parse_args()

    base_url = args.base_url
    concurrency = args.concurrency
    total_sessions = args.sessions

    print(f"Starting load test: {total_sessions} sessions, {concurrency} concurrent")
    print(f"Target: {base_url}")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print()

    results: list[dict] = []
    start_wall = time.monotonic()

    with httpx.Client(base_url=base_url, timeout=TIMEOUT) as shared_client:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(run_session, shared_client, VALID_VINS[i % len(VALID_VINS)], i + 1): i + 1
                for i in range(total_sessions)
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    status = "✓" if result["success"] else "✗"
                    total = result.get("total_ms", 0)
                    sn = result["session_num"]
                    print(f"  [{status}] Session {sn:>3}: {total:>7.1f}ms", flush=True)
                except Exception as exc:
                    results.append({
                        "session_num": futures[future],
                        "success": False,
                        "errors": [f"executor: {exc}"],
                        "timings": {},
                        "total_ms": 0,
                        "steps": 0,
                    })
                    print(f"  [✗] Session {futures[future]:>3}: executor error", flush=True)

    total_duration = time.monotonic() - start_wall
    print_summary(results, total_duration)

    # Return exit code based on success rate
    successes = sum(1 for r in results if r["success"])
    rate = successes / len(results) if results else 0
    if rate >= 0.9:
        print("✅ Load test PASSED (>= 90% success rate)")
        sys.exit(0)
    else:
        print(f"❌ Load test FAILED ({rate:.0%} success rate, need >= 90%)")
        sys.exit(1)


if __name__ == "__main__":
    main()
