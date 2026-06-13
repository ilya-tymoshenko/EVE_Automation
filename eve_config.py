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
    "screens/launcher_add_account_button.png",
    "screens/launcher_username_field.png",
    "screens/launcher_username_label.png",
    "screens/launcher_password_field.png",
    "screens/launcher_password_label.png",
    "screens/launcher_sign_in_button.png",
    "screens/lancher_play_now_button.png",
    "screens/launcher_account_settings_button.png",
    "screens/launcher_button_status_client_is_running.png",
    "screens/launcher_email_verification_code_field.png",
    "screens/launcher_email_verification_continue_button.png",
    "screens/launcher_remove_account_button.png",
    "screens/launcher_remove_account_button_2.png",
    "screens/launcher_fullscreen.png",
    "screens/launcher_fullscreen_ready_status.png",
    "screens/launcher_fullscreen_account_header.png",
    "gift_claim_button.png",
    "screens/game_7_days_omega_offer_in_store_1.png",
    "screens/game_7_days_omega_offer_in_store_3(free button).png",
    "confirm_yes_button.png",
    "license_accept_button.png",
    "screens/game_new_event.png",
    "screens/game_new_event_close_button.png",
    "screens/game_7_days_omega_offer_in_store_2.png",
    "screens/game_log_off_button.png",
    "screens/game_log_off_yes_button.png",
    "screens/game_gift_claim_button.png",
    "screens/game_character_pick.png",
    "screens/game_gifts_button.png",
    "screens/game_gifts_select_all_button.png",
    "screens/game_redeem_to_current_station.png",
    "screens/game_redeem_yes_button.png",
    "screens/game_expert_system_event.png",
    "screens/x2.png",
    "screens/game_skills.png",
    "screens/game_skills2.png",
    "screens/game_skills_menu.png",
    "screens/game_skill_queue_replace_button.png",
    "screens/game_success_skill.png",
    "screens/game_plus_button.png",
    "screens/game_confirm_button.png",
    "screens/game_close1.png",
    "screens/game_close2.png",
    "screens/game_close3.png",
    "screens/game_quit_game_button.png",
    "screens/game_yes_button_after_quit.png",
    "screens/game_reward_popup_title.png",
    "screens/game_undock_button.png",
    "screens/game_ui_setting.png",
    "screens/game_enable_window_blur.png",
]

GAME_CONTRACT_EXTRACTOR_TEMPLATE_ASSETS = [
    "screens/game_menu_button.png",
    "screens/game_finance_button.png",
    "screens/game_contracts_button.png",
    "screens/game_my_contracts_button.png",
    "screens/game_contract_name_button.png",
    "screens/game_contract_accept_button.png",
    "screens/game_contract_yes_button.png",
    "screens/game_contract_close_button.png",
    "screens/x.png",
    "screens/game_inventory_icon.png",
    "screens/game_jita4.png",
    "screens/game_skill_extractor.png",
    "screens/game_activate_skill_extractor.png",
    "screens/game_leave_current_ship_button.png",
    "screens/game_not_enough_skill_points_alert.png",
    "screens/game_skills_engineering.png",
    "screens/game_skill_electronic_upgrades.png",
    "screens/game_skill_weapon_upgrades.png",
    "screens/game_skill_cpu_management.png",
    "screens/game_extract_skill_button.png",
    "screens/game_big_extract_button.png",
    "screens/game_claim_button.png",
    "screens/game_large_skill_injector.png",
    "screens/game_create_contract.png",
    "screens/game_private.png",
    "screens/game_name.png",
    "screens/game_search_by.png",
    "screens/game_exact_phrase_main.png",
    "screens/game_exact_phrase.png",
    "screens/game_only_exact_phrase.png",
    "screens/game_next_button.png",
    "screens/game_type_box.png",
    "screens/game_finish_button.png",
    "screens/game_yes_button.png",
    "screens/success_screen.png",
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
    *GAME_CONTRACT_EXTRACTOR_TEMPLATE_ASSETS,
    *CHARACTER_CREATION_TEMPLATE_ASSETS,
]

REQUIRED_ASSETS = MATCH_TEMPLATE_ASSETS
