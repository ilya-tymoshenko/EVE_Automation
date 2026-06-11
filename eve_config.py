import os
import platform
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DEFAULT_WINDOWS_LAUNCHER_PATH = r"D:\SteamLibrary\steamapps\common\Eve Online\eve-online.exe"
DEFAULT_LINUX_STEAM_APP_ID = "8500"

LINUX_STEAM_EVE_DIR = Path.home() / ".local/share/Steam/steamapps/common/Eve Online"
LINUX_STEAM_EVE_EXE = LINUX_STEAM_EVE_DIR / "eve-online.exe"


def _parse_env_value(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def load_project_env(env_path=None, override=False):
    path = Path(env_path) if env_path else BASE_DIR / ".env"
    if not path.exists():
        return False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        if not key:
            continue

        if override or key not in os.environ:
            os.environ[key] = _parse_env_value(value)
    return True


load_project_env()


def apply_linux_xauthority_fallback():
    if platform.system().lower() != "linux":
        return False
    if not os.environ.get("DISPLAY"):
        return False
    if os.environ.get("XAUTHORITY"):
        return False
    if (Path.home() / ".Xauthority").exists():
        return False

    os.environ["XAUTHORITY"] = "/dev/null"
    return True


def install_wayland_screenshot_backend(pyautogui_module=None):
    if platform.system().lower() != "linux":
        return False
    if not os.environ.get("WAYLAND_DISPLAY"):
        return False

    grim_bin = shutil.which("grim")
    if not grim_bin:
        return False

    from PIL import Image
    import pyscreeze

    def grim_screenshot(imageFilename=None, region=None):
        fd, tmp_filename = tempfile.mkstemp(prefix="eve-automation-", suffix=".png")
        os.close(fd)
        try:
            command = [grim_bin]
            if region is not None:
                x, y, width, height = region
                command.extend(["-g", f"{int(x)},{int(y)} {int(width)}x{int(height)}"])
            command.append(tmp_filename)
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            image = Image.open(tmp_filename)
            image.load()
            if imageFilename is not None:
                image.save(imageFilename)
            return image
        finally:
            try:
                os.unlink(tmp_filename)
            except FileNotFoundError:
                pass

    pyscreeze.screenshot = grim_screenshot
    if pyautogui_module is not None:
        pyautogui_module.screenshot = grim_screenshot
    return True


def resource_path(path_value):
    path = Path(path_value)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def get_launcher_command():
    override = os.environ.get("EVE_LAUNCHER_COMMAND")
    if override:
        return shlex.split(override)

    system = platform.system().lower()
    if system == "windows":
        return [os.environ.get("EVE_LAUNCHER_EXECUTABLE_PATH", DEFAULT_WINDOWS_LAUNCHER_PATH)]

    if system == "linux":
        steam_app_id = os.environ.get("EVE_STEAM_APP_ID", DEFAULT_LINUX_STEAM_APP_ID)
        steam_bin = shutil.which("steam")
        if steam_bin:
            return [steam_bin, "-applaunch", steam_app_id]

        launcher_path = os.environ.get("EVE_LAUNCHER_EXECUTABLE_PATH")
        if launcher_path:
            return [launcher_path]

        return ["steam", "-applaunch", steam_app_id]

    launcher_path = os.environ.get("EVE_LAUNCHER_EXECUTABLE_PATH", DEFAULT_WINDOWS_LAUNCHER_PATH)
    return [launcher_path]


def describe_launcher_command():
    return " ".join(shlex.quote(part) for part in get_launcher_command())


LAUNCHER_TEMPLATE_ASSETS = [
    "add_account_button.png",
    "sign_in_button.png",
    "launcher_play_button.png",
    "gift_claim_button.png",
    "gift_close_button.png",
    "confirm_yes_button.png",
    "license_accept_button.png",
]

CHARACTER_CREATION_TEMPLATE_ASSETS = [
    "caldari_faction_1.png",
    "caldari_faction_2.png",
    "caldari_faction_3.png",
    "caldari_faction_4.png",
    "name.png",
    "character_creation_success_indicator.png",
]

MATCH_TEMPLATE_ASSETS = [
    *LAUNCHER_TEMPLATE_ASSETS,
    *CHARACTER_CREATION_TEMPLATE_ASSETS,
]

REQUIRED_ASSETS = MATCH_TEMPLATE_ASSETS
