#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
MAX_PROMPT_CHARS = 70000
MAX_UNTRACKED_FILE_BYTES = 40000
MAX_UNTRACKED_FILES = 20
LARGE_REVIEW_CHANGED_PATHS = 15
LARGE_REVIEW_DIFF_CHARS = 20000
REVIEW_NOISE_PATHS = {
    "cron/jobs.json",
    "context_length_cache.yaml",
}
REVIEW_NOISE_PREFIXES = (
    "cron/output/",
)
REVIEW_NOISE_SUFFIXES = (
    ".pyc",
)

REPOS = [
    {
        "label": "openclaw config",
        "path": str(Path.home() / ".openclaw"),
    },
    {
        "label": "hermes config",
        "path": str(Path.home() / ".hermes"),
    },
    {
        "label": "PKB",
        "path": "/data/syncthing/obsidian-second-brain",
    },
]


def shutil_which(name: str) -> str | None:
    for base in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(base) / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def resolve_executable(candidate: str | None) -> str | None:
    if not candidate:
        return None
    if os.path.sep not in candidate:
        located = shutil_which(candidate)
        if located:
            return located
    path = Path(candidate).expanduser()
    if path.is_file() and os.access(path, os.X_OK):
        return str(path)
    return None


GEMINI_BIN = None
for candidate in (
    os.environ.get("GEMINI_BIN"),
    shutil_which("gemini"),
    "/data/pnpm/gemini",
    str(Path.home() / ".local" / "bin" / "gemini"),
):
    GEMINI_BIN = resolve_executable(candidate)
    if GEMINI_BIN:
        break


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(shlex.quote(c) for c in cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout


def git(repo: str, *args: str, check: bool = True) -> str:
    return run(["git", "-C", repo, *args], check=check)


def status_lines(repo: str) -> list[str]:
    out = git(repo, "status", "--porcelain=v1")
    return [line for line in out.splitlines() if line.strip()]


def parse_changed_paths(status: list[str]) -> list[str]:
    paths: list[str] = []
    for line in status:
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        if raw:
            paths.append(raw)
    return paths


def parse_untracked_paths(status: list[str]) -> list[str]:
    paths: list[str] = []
    for line in status:
        if not line.startswith("?? "):
            continue
        raw = line[3:]
        if raw:
            paths.append(raw)
    return paths


def is_review_noise(path: str) -> bool:
    if path in REVIEW_NOISE_PATHS:
        return True
    if any(path.startswith(prefix) for prefix in REVIEW_NOISE_PREFIXES):
        return True
    if any(path.endswith(suffix) for suffix in REVIEW_NOISE_SUFFIXES):
        return True
    return "__pycache__/" in path


def filter_review_paths(paths: list[str]) -> list[str]:
    return [path for path in paths if not is_review_noise(path)]


def summarize_diff_for_prompt(diff_text: str, changed_paths: list[str], *, limit: int) -> str:
    if not diff_text:
        return "(none)"
    if len(changed_paths) > LARGE_REVIEW_CHANGED_PATHS or len(diff_text) > LARGE_REVIEW_DIFF_CHARS:
        return (
            "[full patch omitted for model stability: "
            f"{len(changed_paths)} changed paths, {len(diff_text)} diff chars; "
            "use changed paths, git status, diff stats, and untracked previews]"
        )
    return trim_context(diff_text, limit)


def upstream(repo: str) -> str | None:
    out = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False).strip()
    return out or None


def current_branch(repo: str) -> str:
    branch = git(repo, "branch", "--show-current").strip()
    if not branch:
        return "HEAD"
    return branch


def remote_has_branch(repo: str, branch: str) -> bool:
    if not branch or branch == "HEAD":
        return False
    out = git(repo, "ls-remote", "--heads", "origin", branch, check=False).strip()
    return bool(out)


def remote_show(repo: str) -> str:
    return git(repo, "remote", "show", "origin", check=False).strip()


def is_text_file(path: Path) -> bool:
    try:
        data = path.read_bytes()[:4096]
    except Exception:
        return False
    if b"\x00" in data:
        return False
    return True


def build_untracked_preview(repo: str, untracked_paths: list[str]) -> str:
    previews: list[str] = []
    count = 0
    for rel in untracked_paths:
        abs_path = Path(repo) / rel
        if not abs_path.exists() or abs_path.is_dir():
            continue
        if count >= MAX_UNTRACKED_FILES:
            previews.append("[untracked preview truncated: too many files]")
            break
        if abs_path.stat().st_size > MAX_UNTRACKED_FILE_BYTES or not is_text_file(abs_path):
            previews.append(f"--- {rel} (preview omitted: binary or too large) ---")
            count += 1
            continue
        diff = run(["git", "diff", "--no-index", "--", "/dev/null", str(abs_path)], check=False)
        if diff:
            previews.append(diff)
            count += 1
    return "\n".join(previews)


def cleanup_self_bytecode() -> None:
    cache_dir = Path(__file__).resolve().parent / "__pycache__"
    if not cache_dir.exists():
        return
    for pyc_path in cache_dir.glob("gemini_repo_review.*.pyc"):
        try:
            pyc_path.unlink()
        except FileNotFoundError:
            pass
    try:
        next(cache_dir.iterdir())
    except StopIteration:
        try:
            cache_dir.rmdir()
        except OSError:
            pass


def trim_context(text: str, limit: int = MAX_PROMPT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 200] + "\n\n[truncated due to size]\n"


def extract_json(text: str) -> dict[str, Any]:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidates = []
    if match:
        candidates.append(match.group(1))
    start_positions = [m.start() for m in re.finditer(r"\{", text)]
    for start in start_positions:
        depth = 0
        for idx in range(start, len(text)):
            ch = text[idx]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:idx + 1])
                    break
    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    raise ValueError(f"could not parse JSON from Gemini output:\n{text}")


def validate_decision(decision: dict[str, Any], changed_paths: list[str]) -> dict[str, Any]:
    allowed = set(changed_paths)
    action = str(decision.get("action", "noop")).strip().lower()
    include = decision.get("include") or []
    exclude = decision.get("exclude") or []
    commit_message = str(decision.get("commit_message", "")).strip()
    reason = str(decision.get("reason", "")).strip()
    warnings = decision.get("warnings") or []
    if not isinstance(include, list) or not isinstance(exclude, list) or not isinstance(warnings, list):
        raise ValueError(f"invalid Gemini decision structure: {decision}")
    cleaned_include = [str(p) for p in include if str(p) in allowed]
    cleaned_exclude = [str(p) for p in exclude if str(p) in allowed]
    if action != "commit":
        action = "noop"
        cleaned_include = []
        commit_message = ""
    if action == "commit" and (not cleaned_include or not commit_message):
        raise ValueError(f"Gemini requested commit without include files/message: {decision}")
    return {
        "action": action,
        "include": cleaned_include,
        "exclude": cleaned_exclude,
        "commit_message": commit_message,
        "reason": reason,
        "warnings": [str(w) for w in warnings],
    }


def repo_push_mode(repo: str) -> dict[str, str | None]:
    branch = current_branch(repo)
    up = upstream(repo)
    if up:
        return {"branch": branch, "upstream": up, "push_mode": "tracking"}
    if remote_has_branch(repo, branch):
        return {"branch": branch, "upstream": None, "push_mode": "set_upstream"}
    return {"branch": branch, "upstream": None, "push_mode": "unsafe"}


def gemini_review(repo_info: dict[str, str], changed_paths: list[str], untracked_paths: list[str], push_info: dict[str, str | None]) -> dict[str, Any]:
    repo = repo_info["path"]
    status = git(repo, "status", "--short", "--branch")
    diff_stat = git(repo, "diff", "--stat", check=False)
    staged_stat = git(repo, "diff", "--cached", "--stat", check=False)
    diff_excerpt = git(repo, "diff", "--no-ext-diff", check=False)
    staged_excerpt = git(repo, "diff", "--cached", "--no-ext-diff", check=False)
    untracked_excerpt = build_untracked_preview(repo, untracked_paths)
    remote_info = remote_show(repo)
    diff_excerpt_for_prompt = summarize_diff_for_prompt(diff_excerpt, changed_paths, limit=12000)
    staged_excerpt_for_prompt = summarize_diff_for_prompt(staged_excerpt, changed_paths, limit=6000)

    prompt = f"""
You are reviewing one git repository for an unattended nightly backup commit.
Return JSON only, with no markdown or extra commentary, matching exactly this schema:
{{
  "action": "noop" | "commit",
  "include": ["relative/path", "..."],
  "exclude": ["relative/path", "..."],
  "commit_message": "type(scope): summary",
  "reason": "short explanation",
  "warnings": ["optional warning", "..."]
}}

Rules:
- Commit only meaningful, intentional changes.
- Favor configuration, docs, scripts, skills, notes, and PKB content.
- Exclude secrets, credential material, caches, transient logs, cron outputs, bulky generated artifacts, and obviously machine-local noise.
- Never include .env files or credential files.
- If the repo should not be committed now, return action=noop.
- include paths must be selected only from the changed/untracked paths listed below.
- commit_message must be a concise conventional commit message when action=commit.
- If push_mode is unsafe, prefer action=noop unless the context clearly says otherwise.

Repository label: {repo_info['label']}
Repository path: {repo}
Current branch: {push_info['branch']}
Upstream: {push_info['upstream'] or '(none)'}
Push mode: {push_info['push_mode']}

Changed/untracked paths:
{os.linesep.join(changed_paths) if changed_paths else '(none)'}

Git status:
{status}

Unstaged diff stat:
{diff_stat or '(none)'}

Staged diff stat:
{staged_stat or '(none)'}

Remote info:
{remote_info or '(none)'}

Unstaged diff excerpt:
{diff_excerpt_for_prompt}

Staged diff excerpt:
{staged_excerpt_for_prompt}

Untracked file preview:
{trim_context(untracked_excerpt, 8000) or '(none)'}
""".strip()

    output = run(
        [
            GEMINI_BIN,
            "-p",
            trim_context(prompt),
            "--output-format",
            "text",
            "--approval-mode",
            "plan",
        ]
    )
    return extract_json(output)


def stage_and_commit(repo: str, include: list[str], commit_message: str) -> bool:
    git(repo, "reset", "--quiet")
    for path in include:
        git(repo, "add", "-A", "--", path)
    diff_cached = subprocess.run(["git", "-C", repo, "diff", "--cached", "--quiet"])
    if diff_cached.returncode == 0:
        return False
    git(repo, "commit", "-m", commit_message)
    return True


def push_commit(repo: str, push_info: dict[str, str | None]) -> None:
    mode = push_info["push_mode"]
    branch = push_info["branch"]
    if mode == "tracking":
        git(repo, "push")
    elif mode == "set_upstream":
        git(repo, "push", "-u", "origin", branch)
    else:
        raise RuntimeError(f"unsafe push mode for {repo}: {mode}")


def process_repo(repo_info: dict[str, str]) -> dict[str, Any]:
    repo = repo_info["path"]
    if not Path(repo).exists():
        return {"repo": repo_info["label"], "path": repo, "result": "missing"}
    if git(repo, "rev-parse", "--is-inside-work-tree", check=False).strip() != "true":
        return {"repo": repo_info["label"], "path": repo, "result": "not_git"}

    status = status_lines(repo)
    changed = parse_changed_paths(status)
    untracked = parse_untracked_paths(status)
    review_changed = filter_review_paths(changed)
    review_untracked = filter_review_paths(untracked)
    filtered_noise = [path for path in changed if is_review_noise(path)]
    push_info = repo_push_mode(repo)

    if not review_changed:
        result = {
            "repo": repo_info["label"],
            "path": repo,
            "result": "clean",
            "branch": push_info["branch"],
            "push_mode": push_info["push_mode"],
        }
        if filtered_noise:
            result["ignored_noise"] = filtered_noise
        return result

    if push_info["push_mode"] == "unsafe":
        warnings: list[str] = [
            "Skipped Gemini review because push mode is unsafe for unattended automation.",
        ]
        if filtered_noise:
            warnings.append(f"Ignored transient paths before review: {', '.join(filtered_noise)}")
        return {
            "repo": repo_info["label"],
            "path": repo,
            "result": "skipped_unsafe_push",
            "branch": push_info["branch"],
            "push_mode": push_info["push_mode"],
            "pending_paths": review_changed,
            "decision": {
                "action": "noop",
                "include": [],
                "exclude": review_changed,
                "commit_message": "",
                "reason": "Push mode is unsafe, so unattended review/commit is skipped.",
                "warnings": warnings,
            },
        }

    decision = validate_decision(gemini_review(repo_info, review_changed, review_untracked, push_info), review_changed)
    if filtered_noise:
        warnings = list(decision.get("warnings") or [])
        warnings.append(f"Ignored transient paths before review: {', '.join(filtered_noise)}")
        decision["warnings"] = warnings

    if decision["action"] != "commit":
        return {
            "repo": repo_info["label"],
            "path": repo,
            "result": "noop",
            "branch": push_info["branch"],
            "push_mode": push_info["push_mode"],
            "decision": decision,
        }

    if DRY_RUN:
        return {
            "repo": repo_info["label"],
            "path": repo,
            "result": "dry_run_commit",
            "branch": push_info["branch"],
            "push_mode": push_info["push_mode"],
            "decision": decision,
        }

    committed = stage_and_commit(repo, decision["include"], decision["commit_message"])
    if not committed:
        return {
            "repo": repo_info["label"],
            "path": repo,
            "result": "noop_after_stage",
            "branch": push_info["branch"],
            "push_mode": push_info["push_mode"],
            "decision": decision,
        }
    push_commit(repo, push_info)
    commit_hash = git(repo, "rev-parse", "--short", "HEAD").strip()
    return {
        "repo": repo_info["label"],
        "path": repo,
        "result": "committed_and_pushed",
        "branch": push_info["branch"],
        "push_mode": push_info["push_mode"],
        "commit": commit_hash,
        "decision": decision,
    }


def main() -> int:
    cleanup_self_bytecode()

    if not GEMINI_BIN:
        print(json.dumps({"error": "gemini cli not found"}, ensure_ascii=False, indent=2))
        return 1

    results = []
    for repo_info in REPOS:
        try:
            results.append(process_repo(repo_info))
        except Exception as exc:
            results.append(
                {
                    "repo": repo_info["label"],
                    "path": repo_info["path"],
                    "result": "error",
                    "error": str(exc),
                }
            )

    payload = {
        "dry_run": DRY_RUN,
        "gemini_bin": GEMINI_BIN,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if all(r.get("result") != "error" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
