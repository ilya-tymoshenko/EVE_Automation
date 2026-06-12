import importlib
import importlib.util
import os
import platform
import shutil
from pathlib import Path

from eve_config import (
    LINUX_STEAM_EVE_EXE,
    REQUIRED_ASSETS,
    apply_linux_xauthority_fallback,
    describe_launcher_command,
    get_launcher_command,
    install_wayland_screenshot_backend,
    resource_path,
)


REQUIRED_MODULES = [
    "pyautogui",
    "pyperclip",
    "cv2",
    "PIL",
    "bs4",
    "requests",
    "google_auth_oauthlib",
    "googleapiclient",
]


def module_available(module_name):
    return importlib.util.find_spec(module_name) is not None


def module_import_status(module_name):
    if not module_available(module_name):
        return "missing", None
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        return "import failed", f"{type(exc).__name__}: {exc}"
    return "ok", None


def main():
    xauthority_fallback_applied = apply_linux_xauthority_fallback()

    print("== EVE Automation preflight ==")
    print(f"Platform: {platform.platform()}")
    print(f"Session: XDG_SESSION_TYPE={os.environ.get('XDG_SESSION_TYPE', '')}")
    print(f"DISPLAY={os.environ.get('DISPLAY', '')}")
    print(f"WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY', '')}")
    print(f"XAUTHORITY={os.environ.get('XAUTHORITY', '')}")
    if xauthority_fallback_applied:
        print("XAUTHORITY fallback applied: /dev/null")
    print()

    print("Env secrets:")
    secret_vars = [
        "EVE_ACCOUNT_PASSWORD",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GMAIL_REFRESH_TOKEN",
        "OPENAI_API_KEY",
    ]
    missing_secret_vars = []
    for var_name in secret_vars:
        is_set = bool(os.environ.get(var_name))
        print(f"  {var_name}: {'set' if is_set else 'missing'}")
        if not is_set:
            missing_secret_vars.append(var_name)
    print()

    print("Launcher command:")
    print(f"  {describe_launcher_command()}")
    command = get_launcher_command()
    if command and shutil.which(command[0]) is None and not Path(command[0]).exists():
        print(f"  WARNING: command executable not found: {command[0]}")
    if platform.system().lower() == "linux":
        print(f"  Steam EVE executable present: {LINUX_STEAM_EVE_EXE.exists()} ({LINUX_STEAM_EVE_EXE})")
    print()

    print("Window focus:")
    print(f"  niri: {'ok' if shutil.which('niri') else 'missing'}")
    print()

    print("Python modules:")
    failed_modules = []
    for module_name in REQUIRED_MODULES:
        status, error = module_import_status(module_name)
        print(f"  {module_name}: {status}")
        if error:
            print(f"    {error}")
        if status != "ok":
            failed_modules.append(module_name)
    print()

    print("Assets:")
    missing_assets = []
    for asset_name in REQUIRED_ASSETS:
        asset_path = resource_path(asset_name)
        ok = asset_path.exists()
        print(f"  {asset_name}: {'ok' if ok else 'missing'}")
        if not ok:
            missing_assets.append(asset_name)
    print()

    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        print("WARNING: Wayland is active. PyAutoGUI screen search/input may be unreliable; X11 is safer for this project.")
    if missing_secret_vars:
        print("WARNING: missing env secrets can block Gmail or account login flows.")
    if failed_modules:
        print("WARNING: fix missing or non-importable Python modules before running GUI automation.")
    if missing_assets:
        print("WARNING: missing image assets block screen matching.")

    print()
    print("OpenAI API repair:")
    openai_module_status, openai_module_error = module_import_status("openai")
    runner_path = resource_path("run_with_codex_repair.py")
    schema_path = resource_path("codex_repair_schema.json")
    print(f"  openai module: {openai_module_status}")
    if openai_module_error:
        print(f"    {openai_module_error}")
    print(f"  runner: {'ok' if runner_path.exists() else 'missing'} ({runner_path})")
    print(f"  schema: {'ok' if schema_path.exists() else 'missing'} ({schema_path})")
    api_repair_missing = openai_module_status != "ok" or not runner_path.exists() or not schema_path.exists()
    if api_repair_missing:
        print("WARNING: OpenAI API repair runner is incomplete; the base bot can still run without it.")

    screenshot_failed = False
    if "pyautogui" not in failed_modules:
        print()
        print("Screen capture:")
        try:
            import pyautogui

            backend_applied = install_wayland_screenshot_backend(pyautogui)
            screenshot = pyautogui.screenshot()
            print(f"  screenshot: ok {screenshot.size} {screenshot.mode}")
            if backend_applied:
                print("  backend: grim")
        except Exception as exc:
            screenshot_failed = True
            print(f"  screenshot: failed ({type(exc).__name__}: {exc})")

    if failed_modules or missing_assets or screenshot_failed:
        raise SystemExit(1)

    print("Preflight passed.")


if __name__ == "__main__":
    main()
