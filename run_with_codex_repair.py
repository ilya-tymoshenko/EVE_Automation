import argparse
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from eve_config import load_project_env

PROJECT_DIR = Path(__file__).resolve().parent
BOT_SCRIPT = PROJECT_DIR / "eve_bot.py"
PREFLIGHT_SCRIPT = PROJECT_DIR / "preflight.py"
SCHEMA_PATH = PROJECT_DIR / "codex_repair_schema.json"
FAILURE_DIR = PROJECT_DIR / "runtime_failures"
REPORT_DIR = PROJECT_DIR / "codex_reports"

DEFAULT_REPAIR_MODEL = "gpt-5.5"
DEFAULT_SOURCE_FILES = [
    "eve_bot.py",
    "eve_config.py",
    "mail.py",
    "preflight.py",
    "requirements.txt",
]
MAX_SOURCE_CHARS_PER_FILE = int(os.environ.get("OPENAI_REPAIR_MAX_SOURCE_CHARS_PER_FILE", "35000"))
MAX_LOG_TAIL_CHARS = int(os.environ.get("OPENAI_REPAIR_MAX_LOG_TAIL_CHARS", "20000"))

load_project_env()


REDACTION_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r"GO" r"CSPX-[A-Za-z0-9_\-]{16,}"), "[REDACTED_GOOGLE_CLIENT_SECRET]"),
    (re.compile(r"ya29\.[A-Za-z0-9_\-\.]+"), "[REDACTED_GOOGLE_ACCESS_TOKEN]"),
    (re.compile(r"1/" r"/[A-Za-z0-9_\-]+"), "[REDACTED_GOOGLE_REFRESH_TOKEN]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9_\-\.]+"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(password\s*[:=]\s*)\S+"), r"\1[REDACTED_PASSWORD]"),
    (re.compile(r"(?i)(secret\s*[:=]\s*)\S+"), r"\1[REDACTED_SECRET]"),
    (re.compile(r"(?i)(token\s*[:=]\s*)\S+"), r"\1[REDACTED_TOKEN]"),
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


def latest_failure_context():
    if not FAILURE_DIR.exists():
        return None
    candidates = sorted(
        FAILURE_DIR.glob("failure_context_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def redact_text(value):
    if not isinstance(value, str):
        return value

    redacted = value
    for pattern, replacement in REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def sanitize_value(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if key.lower() in {"token", "refresh_token", "access_token", "client_secret", "password", "secret"}:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_value(item)
        return sanitized

    if isinstance(value, list):
        return [sanitize_value(item) for item in value]

    return redact_text(value)


def safe_context_for_prompt(context):
    safe_context = {
        "timestamp": context.get("timestamp"),
        "reason": context.get("reason"),
        "exit_code": context.get("exit_code"),
        "current_account_number": context.get("current_account_number"),
        "last_account_for_termination": context.get("last_account_for_termination"),
        "next_start_account_hint": context.get("next_start_account_hint"),
        "launcher_command": context.get("launcher_command"),
        "platform": context.get("platform"),
        "session": context.get("session"),
        "log_file": context.get("log_file"),
        "log_tail": context.get("log_tail", "")[-MAX_LOG_TAIL_CHARS:],
        "screenshot_path": context.get("screenshot_path"),
        "screenshot_error": context.get("screenshot_error"),
        "exception": context.get("exception"),
    }
    return sanitize_value(safe_context)


def source_file_names():
    raw_value = os.environ.get("OPENAI_REPAIR_SOURCE_FILES", "")
    if not raw_value.strip():
        return DEFAULT_SOURCE_FILES
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def safe_source_path(relative_name):
    path = (PROJECT_DIR / relative_name).resolve()
    try:
        path.relative_to(PROJECT_DIR)
    except ValueError as exc:
        raise ValueError(f"Source path escapes project directory: {relative_name}") from exc
    return path


def read_source_context():
    files = []
    for relative_name in source_file_names():
        path = safe_source_path(relative_name)
        if not path.exists() or not path.is_file():
            files.append({"path": relative_name, "missing": True})
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        truncated = len(text) > MAX_SOURCE_CHARS_PER_FILE
        if truncated:
            text = text[:MAX_SOURCE_CHARS_PER_FILE] + "\n<TRUNCATED>\n"

        files.append(
            {
                "path": relative_name,
                "missing": False,
                "truncated": truncated,
                "content": sanitize_value(text),
            }
        )
    return files


def repair_instructions():
    return (
        "Ты AI repair analyst для локального проекта EVE_Automation.\n"
        "Сценарий: основной GUI-бот остановился с ошибкой. Нужно разобраться по crash context, "
        "логу, исходникам и скриншоту, затем вернуть JSON строго по заданной схеме.\n\n"
        "Правила безопасности:\n"
        "- Не запускай EVE, Steam или GUI-бот.\n"
        "- Не проси и не выводи секреты, токены, пароли или содержимое .env.\n"
        "- Не предлагай destructive git/reset/rm операции.\n"
        "- Указывай только минимальные правки, относящиеся к причине сбоя.\n"
        "- Этот API runner не применяет патчи автоматически; changed_files означает файлы, которые нужно изменить человеку/агенту.\n"
        "- restart_safe=true ставь только если правки не нужны, либо проблема явно конфигурационная и повторный запуск безопасен.\n"
        "- Если причина не подтверждена, нужна живая проверка в игре или нужны правки кода, ставь restart_safe=false и requires_human_review=true.\n"
        "- next_start_account обычно равен next_start_account_hint/current_account_number из контекста, если нужно повторить тот же аккаунт."
    )


def build_repair_payload(context_path, context):
    return {
        "project": "EVE_Automation",
        "context_path": str(context_path),
        "schema_path": str(SCHEMA_PATH),
        "crash_context": safe_context_for_prompt(context),
        "source_files": read_source_context(),
    }


def screenshot_input_part(context):
    screenshot_path = context.get("screenshot_path")
    if not screenshot_path:
        return None

    path = Path(screenshot_path)
    if not path.exists() or not path.is_file():
        return None

    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "input_image",
        "image_url": f"data:{mime_type};base64,{encoded}",
        "detail": "high",
    }


def normalize_schema_for_openai(schema):
    if isinstance(schema, dict):
        normalized = {}
        for key, value in schema.items():
            if key == "$schema":
                continue
            if key == "type" and isinstance(value, list):
                normalized["anyOf"] = [{"type": item} for item in value]
                continue
            normalized[key] = normalize_schema_for_openai(value)
        return normalized

    if isinstance(schema, list):
        return [normalize_schema_for_openai(item) for item in schema]

    return schema


def repair_response_format():
    return {
        "format": {
            "type": "json_schema",
            "name": "eve_repair_report",
            "schema": normalize_schema_for_openai(load_json(SCHEMA_PATH)),
            "strict": True,
        }
    }


def repair_model():
    return os.environ.get("OPENAI_REPAIR_MODEL", DEFAULT_REPAIR_MODEL)


def repair_timeout():
    raw_value = os.environ.get("OPENAI_REPAIR_TIMEOUT_SECONDS", "120")
    try:
        return float(raw_value)
    except ValueError:
        return 120.0


def max_output_tokens():
    raw_value = os.environ.get("OPENAI_REPAIR_MAX_OUTPUT_TOKENS", "2000")
    try:
        value = int(raw_value)
    except ValueError:
        return 2000
    return value if value > 0 else 2000


def build_api_request(context_path):
    context = load_json(context_path)
    payload = build_repair_payload(context_path, context)
    content = [
        {
            "type": "input_text",
            "text": (
                "Analyze this crash context and source snapshot. Return only the structured repair report.\n\n"
                f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
            ),
        }
    ]

    image_part = screenshot_input_part(context)
    if image_part:
        content.append(image_part)

    return {
        "model": repair_model(),
        "instructions": repair_instructions(),
        "input": [{"role": "user", "content": content}],
        "text": repair_response_format(),
        "max_output_tokens": max_output_tokens(),
    }


def validate_report(report):
    required_fields = {
        "summary": str,
        "root_cause": str,
        "changed_files": list,
        "verification": list,
        "restart_safe": bool,
        "requires_human_review": bool,
        "notes": str,
    }

    if not isinstance(report, dict):
        raise ValueError("repair report is not a JSON object")

    for field_name, expected_type in required_fields.items():
        if field_name not in report:
            raise ValueError(f"repair report missing field: {field_name}")
        if not isinstance(report[field_name], expected_type):
            raise ValueError(f"repair report field {field_name} has invalid type")

    if "next_start_account" not in report:
        raise ValueError("repair report missing field: next_start_account")
    if report["next_start_account"] is not None and not isinstance(report["next_start_account"], int):
        raise ValueError("repair report field next_start_account has invalid type")

    if not all(isinstance(item, str) for item in report["changed_files"]):
        raise ValueError("repair report changed_files must contain only strings")
    if not all(isinstance(item, str) for item in report["verification"]):
        raise ValueError("repair report verification must contain only strings")


def fallback_report(error, context_path):
    context = load_json(context_path)
    return {
        "summary": "OpenAI API repair request failed.",
        "root_cause": f"{type(error).__name__}: {error}",
        "changed_files": [],
        "verification": [],
        "restart_safe": False,
        "next_start_account": context.get("next_start_account_hint"),
        "requires_human_review": True,
        "notes": "The bot was not restarted because the API repair report could not be produced or validated.",
    }


def write_report(output_path, report):
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_api_repair(context_path, dry_run=False):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = REPORT_DIR / f"openai_repair_{timestamp}.json"
    request_payload = build_api_request(context_path)

    if dry_run:
        context = load_json(context_path)
        dry_run_summary = {
            "mode": "openai_responses_api",
            "model": request_payload["model"],
            "context_path": str(context_path),
            "output_path": str(output_path),
            "source_files": source_file_names(),
            "screenshot_included": screenshot_input_part(context) is not None,
            "max_output_tokens": request_payload["max_output_tokens"],
        }
        print(json.dumps(dry_run_summary, ensure_ascii=False, indent=2))
        return 0, output_path

    try:
        from openai import OpenAI

        client = OpenAI(timeout=repair_timeout())
        print(f"[runner] running OpenAI API repair with model={request_payload['model']}. Report: {output_path}")
        response = client.responses.create(**request_payload)
        report = json.loads(response.output_text)
        validate_report(report)
    except Exception as exc:
        report = fallback_report(exc, context_path)
        write_report(output_path, report)
        print(f"[runner] OpenAI API repair failed: {type(exc).__name__}: {exc}")
        print(f"[runner] fallback report saved: {output_path}")
        return 1, output_path

    write_report(output_path, report)
    return 0, output_path


def read_repair_report(output_path):
    if not output_path or not output_path.exists():
        return None
    try:
        return load_json(output_path)
    except Exception as exc:
        print(f"[runner] failed to read repair report: {type(exc).__name__}: {exc}")
        return None


def choose_next_start_account(report, context_path):
    if report and report.get("next_start_account"):
        return report["next_start_account"]
    context = load_json(context_path)
    return context.get("next_start_account_hint")


def repair_existing_context(args):
    context_path = args.context or latest_failure_context()
    if not context_path:
        print("[runner] no failure context found.")
        return 1

    code, output_path = run_api_repair(context_path, dry_run=args.dry_run)
    if args.dry_run:
        return code

    report = read_repair_report(output_path)
    print(json.dumps(report, ensure_ascii=False, indent=2) if report else "[runner] no report")
    return code if code != 0 else 0


def run_bot(start_account):
    env = os.environ.copy()
    if start_account:
        env["EVE_START_ACCOUNT"] = str(start_account)
    command = [sys.executable, str(BOT_SCRIPT)]
    print(f"[runner] start bot: {' '.join(command)}")
    if start_account:
        print(f"[runner] EVE_START_ACCOUNT={start_account}")
    return subprocess.run(command, cwd=PROJECT_DIR, env=env)


def run_preflight():
    command = [sys.executable, str(PREFLIGHT_SCRIPT)]
    print(f"[runner] preflight: {' '.join(command)}")
    return subprocess.run(command, cwd=PROJECT_DIR)


def main():
    parser = argparse.ArgumentParser(description="Run EVE bot and ask OpenAI API for a structured repair report after bot failures.")
    parser.add_argument(
        "--max-repair-cycles",
        type=int,
        default=int(os.environ.get("OPENAI_REPAIR_MAX_CYCLES", os.environ.get("EVE_CODEX_MAX_REPAIR_CYCLES", "1"))),
    )
    parser.add_argument(
        "--codex-sandbox",
        choices=["read-only", "workspace-write"],
        default=os.environ.get("EVE_CODEX_SANDBOX", "workspace-write"),
        help="Deprecated compatibility flag. The OpenAI API repair runner does not use a sandbox.",
    )
    parser.add_argument("--no-auto-restart", action="store_true")
    parser.add_argument("--repair-existing", action="store_true", help="Run OpenAI API repair on an existing failure context without launching the bot first.")
    parser.add_argument("--context", type=Path, help="Specific failure_context_*.json path.")
    parser.add_argument("--dry-run", action="store_true", help="Print safe OpenAI API request metadata without calling the API.")
    args = parser.parse_args()

    if args.codex_sandbox:
        pass

    if args.dry_run or args.repair_existing:
        return repair_existing_context(args)

    start_account = os.environ.get("EVE_START_ACCOUNT")
    for repair_cycle in range(args.max_repair_cycles + 1):
        bot_result = run_bot(start_account)
        if bot_result.returncode == 0:
            print("[runner] bot finished successfully.")
            return 0
        if bot_result.returncode == 130:
            print("[runner] bot stopped by user; OpenAI API repair will not run.")
            return 130

        context_path = latest_failure_context()
        if not context_path:
            print(f"[runner] bot failed with exit code {bot_result.returncode}, but no failure context was found.")
            return bot_result.returncode

        if repair_cycle >= args.max_repair_cycles:
            print(f"[runner] repair cycle limit reached. Latest context: {context_path}")
            return bot_result.returncode

        repair_code, output_path = run_api_repair(context_path)
        if repair_code != 0:
            print(f"[runner] OpenAI API repair failed with exit code {repair_code}.")
            return repair_code

        report = read_repair_report(output_path)
        if not report:
            return 1

        print("[runner] OpenAI API repair report:")
        print(json.dumps(report, ensure_ascii=False, indent=2))

        if report.get("requires_human_review") or not report.get("restart_safe"):
            print("[runner] OpenAI API report did not mark restart as safe; stopping for review.")
            return 1

        preflight_result = run_preflight()
        if preflight_result.returncode != 0:
            print(f"[runner] preflight failed after repair report with exit code {preflight_result.returncode}.")
            return preflight_result.returncode

        start_account = choose_next_start_account(report, context_path)
        if args.no_auto_restart:
            print(f"[runner] auto-restart disabled. Suggested EVE_START_ACCOUNT={start_account}")
            return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
