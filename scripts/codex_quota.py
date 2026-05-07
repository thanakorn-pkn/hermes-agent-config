#!/usr/bin/env python3
"""Check Codex quota by driving the interactive TUI and parsing /status.

This script intentionally uses a temporary git repository because Codex's
interactive TUI expects to run inside a repo. It launches Codex in a PTY,
accepts the trust prompt, opens /status, and extracts the 5h + weekly quota
lines into JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
FIVE_H_RE = re.compile(r"5h limit:\s+\[[^\]]*\]\s+(\d+)% left\s+\(resets\s+([^\)]+)\)")
WEEKLY_RE = re.compile(r"Weekly limit:\s+\[[^\]]*\]\s+(\d+)% left\s+\(resets\s+([^\)]+)\)")
ACCOUNT_RE = re.compile(r"Account:\s+(.+?)\s*$", re.MULTILINE)
MODEL_RE = re.compile(r"Model:\s+(.+?)\s*$", re.MULTILINE)
SESSION_RE = re.compile(r"Session:\s+([0-9a-fA-F-]+)\s*$", re.MULTILINE)
USAGE_URL = "https://chatgpt.com/codex/settings/usage"


@dataclass
class QuotaResult:
    account: str | None
    model: str | None
    session: str | None
    five_hour_pct_left: int | None
    five_hour_resets: str | None
    weekly_pct_left: int | None
    weekly_resets: str | None
    usage_url: str
    raw: str


class TimeoutError(RuntimeError):
    pass


def strip_noise(text: str) -> str:
    text = ANSI_RE.sub("", text)
    text = CTRL_RE.sub("", text)
    return text


def find_codex_binary() -> str:
    env_path = os.environ.get("PATH", "")
    augmented = "/data/pnpm:" + env_path if "/data/pnpm" not in env_path.split(":") else env_path
    for candidate in (shutil.which("codex", path=augmented), "/data/pnpm/codex"):
        if candidate and os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise SystemExit("codex binary not found (tried PATH and /data/pnpm/codex)")


def wait_for_capture(session: str, predicate, timeout: float, label: str) -> str:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session, "-p", "-S", "-400"],
            capture_output=True,
            text=True,
            check=False,
        )
        last = result.stdout or ""
        if predicate(strip_noise(last)):
            return last
        time.sleep(0.25)
    raise TimeoutError(f"timed out waiting for {label}")


def tmux_send(session: str, keys: str) -> None:
    subprocess.run(["tmux", "send-keys", "-t", session, keys], check=True)


def launch_codex(repo: str, codex_bin: str, extra_args: list[str] | None = None):
    extra_args = extra_args or []
    session = f"codex-quota-{os.getpid()}-{int(time.time())}"
    env = os.environ.copy()
    env["PATH"] = "/data/pnpm:" + env.get("PATH", "")
    joined = " ".join(shlex.quote(arg) for arg in [codex_bin, "--no-alt-screen", *extra_args])
    tmux_cmd = f"cd {shlex.quote(repo)} && {joined}"
    subprocess.run(["tmux", "new-session", "-d", "-s", session, "-x", "140", "-y", "40", "bash", "-ic", tmux_cmd], check=True, env=env)
    return session


def parse_quota(text: str) -> QuotaResult:
    clean = strip_noise(text)
    account_match = ACCOUNT_RE.search(clean)
    model_match = MODEL_RE.search(clean)
    session_match = SESSION_RE.search(clean)
    five = FIVE_H_RE.search(clean)
    weekly = WEEKLY_RE.search(clean)

    return QuotaResult(
        account=account_match.group(1).strip() if account_match else None,
        model=model_match.group(1).strip() if model_match else None,
        session=session_match.group(1).strip() if session_match else None,
        five_hour_pct_left=int(five.group(1)) if five else None,
        five_hour_resets=five.group(2).strip() if five else None,
        weekly_pct_left=int(weekly.group(1)) if weekly else None,
        weekly_resets=weekly.group(2).strip() if weekly else None,
        usage_url=USAGE_URL,
        raw=clean,
    )


def epoch_to_local(ts: int | float | None) -> str | None:
    if ts is None:
        return None
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(ts))
    except Exception:
        return None


def load_quota_from_logs() -> dict | None:
    sessions_root = Path.home() / ".codex" / "sessions"
    if not sessions_root.exists():
        return None

    jsonl_files = [p for p in sessions_root.rglob("*.jsonl") if p.is_file()]
    jsonl_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    for path in jsonl_files:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            continue

        for line in reversed(lines[-300:]):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "event_msg":
                continue
            payload = obj.get("payload") or {}
            if payload.get("type") != "token_count":
                continue
            rate_limits = payload.get("rate_limits")
            if not rate_limits:
                continue

            primary = rate_limits.get("primary") or {}
            secondary = rate_limits.get("secondary") or {}
            return {
                "source": "session-log",
                "source_file": str(path),
                "timestamp": obj.get("timestamp"),
                "plan_type": rate_limits.get("plan_type"),
                "primary": {
                    "used_percent": primary.get("used_percent"),
                    "left_percent": None if primary.get("used_percent") is None else round(100 - float(primary["used_percent"])),
                    "window_minutes": primary.get("window_minutes"),
                    "resets_at_epoch": primary.get("resets_at"),
                    "resets_at_local": epoch_to_local(primary.get("resets_at")),
                },
                "secondary": {
                    "used_percent": secondary.get("used_percent"),
                    "left_percent": None if secondary.get("used_percent") is None else round(100 - float(secondary["used_percent"])),
                    "window_minutes": secondary.get("window_minutes"),
                    "resets_at_epoch": secondary.get("resets_at"),
                    "resets_at_local": epoch_to_local(secondary.get("resets_at")),
                },
                "credits": rate_limits.get("credits"),
                "rate_limit_reached_type": rate_limits.get("rate_limit_reached_type"),
            }
    return None


def check_quota(timeout: float = 60.0, extra_args: list[str] | None = None) -> QuotaResult:
    codex_bin = find_codex_binary()
    repo = tempfile.mkdtemp(prefix="codex-quota-")
    session = None
    try:
        subprocess.run(["git", "init", "-q", repo], check=True)
        session = launch_codex(repo, codex_bin, extra_args=extra_args)

        # Trust prompt.
        wait_for_capture(session, lambda t: "Press enter to continue" in t or "Yes, continue" in t, timeout=20, label="trust prompt")
        tmux_send(session, "Enter")

        # Wait until the Codex banner appears.
        wait_for_capture(session, lambda t: "OpenAI Codex" in t, timeout=20, label="Codex banner")

        # Ask for status.
        tmux_send(session, "/status")
        tmux_send(session, "Enter")

        # Read until both quota lines are present.
        raw = wait_for_capture(
            session,
            lambda t: FIVE_H_RE.search(t) is not None and WEEKLY_RE.search(t) is not None,
            timeout=timeout,
            label="quota screen",
        )
        return parse_quota(raw)
    finally:
        if session is not None:
            subprocess.run(["tmux", "kill-session", "-t", session], check=False)
        shutil.rmtree(repo, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Codex quota via interactive /status")
    parser.add_argument("--timeout", type=float, default=60.0, help="Seconds to wait for the quota screen")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    log_payload = load_quota_from_logs()
    if log_payload is not None:
        if args.json:
            print(json.dumps(log_payload, ensure_ascii=False))
        else:
            print(json.dumps(log_payload, ensure_ascii=False, indent=2))
        return 0

    try:
        result = check_quota(timeout=args.timeout)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1

    payload = {
        "source": "interactive-tui",
        "account": result.account,
        "model": result.model,
        "session": result.session,
        "five_hour_pct_left": result.five_hour_pct_left,
        "five_hour_resets": result.five_hour_resets,
        "weekly_pct_left": result.weekly_pct_left,
        "weekly_resets": result.weekly_resets,
        "usage_url": result.usage_url,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
