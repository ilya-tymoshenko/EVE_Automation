import json
import os
import platform
import sys
import traceback

from eve_config import apply_linux_xauthority_fallback, install_wayland_screenshot_backend

apply_linux_xauthority_fallback()

import pyautogui
install_wayland_screenshot_backend(pyautogui)
import time
import pyperclip
import random
import datetime
import subprocess
import shutil

from eve_config import describe_launcher_command, get_launcher_command, resource_path
from mail import find_latest_eve_verification_code, get_gmail_service

# --- Пользовательские настройки ---
SKILLS_FILE_PATH = "skills.txt"
LOG_FILE_PATH = "script_run_log.txt" # Логи будут писаться сюда непрерывно
FAILURE_CONTEXT_DIR = "runtime_failures"


def env_list(name, default):
    return [
        item.strip().lower()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


# --- КОНСТАНТЫ ЗАДЕРЖЕК (в секундах) ---
# ВАШИ ОТКАЛИБРОВАННЫЕ ЗНАЧЕНИЯ (оставлены без изменений)
PAUSE_INITIAL_LAUNCHER_LOAD = 3
PAUSE_RESTART_LAUNCHER_LOAD = 4
PAUSE_AFTER_F11_ATTEMPT = 1
PAUSE_BEFORE_F11_ATTEMPT = 1
PAUSE_AFTER_LAUNCHER_FIRST_START = 2
PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC = 4
PAUSE_BETWEEN_UNBUG_CLICKS = 1.0
PAUSE_AFTER_UNBUG_CLICKS = 1.0
PAUSE_SHORT = 0.5
PAUSE_MEDIUM = 1.0
PAUSE_LONG = 1.0
PAUSE_VERY_LONG = 1.0
PAUSE_AFTER_ADD_ACCOUNT_CLICK = 1.0
PAUSE_AFTER_USERNAME_TYPE = 1.0
PAUSE_AFTER_PASSWORD_TYPE = 1.0
PAUSE_AFTER_SIGN_IN_CLICK = 1.0
PAUSE_AFTER_PLAY_CLICK_FOR_GAME_LOAD = 18
PAUSE_CC_AFTER_FACTION_SELECT = 2.5
PAUSE_CC_AFTER_ORIGIN_SELECT = 1.0
PAUSE_CC_AFTER_RACE_SELECT = 2.5
PAUSE_CC_AFTER_EDIT_APPEARANCE = 3.0
PAUSE_CC_AFTER_NEXT_BUTTON = 2.0
PAUSE_CC_AFTER_NAME_FIELD_CLICK = 1.0
PAUSE_CC_AFTER_NAME_TYPE = 1.0
PAUSE_CC_AFTER_ENTER_GAME_BUTTON = 5.0
PAUSE_CC_AFTER_SPACE_PRESS_IN_INTRO = 10.0
PAUSE_CC_AFTER_ESC_IN_INTRO = 1.0
PAUSE_CC_AFTER_SKIP_TUTORIAL_CLICK = 1.0
PAUSE_CC_AFTER_SKIP_TUTORIAL_CONFIRM = 1.0
PAUSE_CC_WAIT_FOR_STATION_LOAD = 10.0
PAUSE_SKILLS_AFTER_OPEN_WINDOW = 1.0
PAUSE_SKILLS_AFTER_PERSONAL_TAB = 1.0
PAUSE_SKILLS_AFTER_CREATE_PLAN = 1.0
PAUSE_SKILLS_AFTER_OPEN_MENU = 1.0
PAUSE_SKILLS_AFTER_PASTE_IMPORT = 0.5
PAUSE_SKILLS_AFTER_IMPORT_CLICK = 1.0
PAUSE_SKILLS_AFTER_PLAN_NAME_CLICK = 1.0
PAUSE_SKILLS_AFTER_PLAN_NAME_TYPE = 1.0
PAUSE_SKILLS_AFTER_SAVE_PLAN = 1.0
PAUSE_SKILLS_AFTER_SELECT_PLAN = 1.0
PAUSE_SKILLS_AFTER_START_TRAINING = 1.5
PAUSE_BEFORE_SUCCESS_VERIFICATION = 1.0
PAUSE_SUCCESS_VERIFICATION_TIMEOUT = 5
PAUSE_AFTER_INGAME_ESC_PRESS = 1.0
PAUSE_AFTER_LOGOUT_BUTTON_CLICK = 1.0
PAUSE_AFTER_QUIT_GAME_CLICK = 1.0
PAUSE_FOR_GAME_TO_CLOSE = 5.0
PAUSE_FOR_GAME_TO_CLOSE_EMERGENCY = 5.0
PAUSE_BEFORE_ACCOUNT_DELETION_ACTIONS = 2.0
PAUSE_AFTER_ACCOUNT_SETTINGS_CLICK = 1
PAUSE_AFTER_REMOVE_ACCOUNT_CLICK = 1
PAUSE_AFTER_CONFIRM_REMOVE_CLICK = 1
PAUSE_BETWEEN_ACCOUNTS_PROCESSING = 2

TIMEOUT_LAUNCHER_READY = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_READY", "120"))
TIMEOUT_LOGIN_DIALOG_READY = int(os.environ.get("EVE_TIMEOUT_LOGIN_DIALOG_READY", "60"))
TIMEOUT_AFTER_SIGN_IN_READY = int(os.environ.get("EVE_TIMEOUT_AFTER_SIGN_IN_READY", "120"))
TIMEOUT_GAME_LAUNCH_VERIFICATION = int(os.environ.get("EVE_TIMEOUT_GAME_LAUNCH_VERIFICATION", "120"))
TIMEOUT_EMAIL_VERIFICATION_PAGE = int(os.environ.get("EVE_TIMEOUT_EMAIL_VERIFICATION_PAGE", "20"))
TIMEOUT_EMAIL_VERIFICATION_CODE = int(os.environ.get("EVE_TIMEOUT_EMAIL_VERIFICATION_CODE", "120"))
EMAIL_VERIFICATION_POLL_SECONDS = int(os.environ.get("EVE_EMAIL_VERIFICATION_POLL_SECONDS", "5"))
EMAIL_VERIFICATION_REQUEST_SKEW_SECONDS = int(os.environ.get("EVE_EMAIL_VERIFICATION_REQUEST_SKEW_SECONDS", "5"))
TIMEOUT_GAME_READY_FOR_INPUT = int(os.environ.get("EVE_TIMEOUT_GAME_READY_FOR_INPUT", "180"))
TIMEOUT_GAME_POPUP_SCAN = int(os.environ.get("EVE_TIMEOUT_GAME_POPUP_SCAN", "2"))
TIMEOUT_GAME_POPUP_QUICK_SCAN = int(os.environ.get("EVE_TIMEOUT_GAME_POPUP_QUICK_SCAN", "1"))
TIMEOUT_GAME_REQUIRED_ACTION = int(os.environ.get("EVE_TIMEOUT_GAME_REQUIRED_ACTION", "15"))
TIMEOUT_GAME_REQUIRED_STATE = int(os.environ.get("EVE_TIMEOUT_GAME_REQUIRED_STATE", "20"))
TIMEOUT_GAME_OPTIONAL_ACTION = int(os.environ.get("EVE_TIMEOUT_GAME_OPTIONAL_ACTION", "4"))
TIMEOUT_GAME_QUIT_MENU_READY = int(os.environ.get("EVE_TIMEOUT_GAME_QUIT_MENU_READY", "25"))
TIMEOUT_GAME_EXIT_TO_LAUNCHER = int(os.environ.get("EVE_TIMEOUT_GAME_EXIT_TO_LAUNCHER", "120"))
TIMEOUT_LAUNCHER_RECOVERY = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_RECOVERY", "90"))
TIMEOUT_LAUNCHER_FOCUS_VERIFY = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_FOCUS_VERIFY", "4"))
TIMEOUT_LAUNCHER_ACCOUNT_REMOVAL_READY = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_ACCOUNT_REMOVAL_READY", "3"))
TIMEOUT_OPTIONAL_CONFIRM_DIALOG = int(os.environ.get("EVE_TIMEOUT_OPTIONAL_CONFIRM_DIALOG", "4"))
MAX_GAME_POPUP_CLOSE_ATTEMPTS = int(os.environ.get("EVE_MAX_GAME_POPUP_CLOSE_ATTEMPTS", "4"))
MAX_GAME_QUIT_MENU_ATTEMPTS = int(os.environ.get("EVE_MAX_GAME_QUIT_MENU_ATTEMPTS", "4"))
MAX_GAME_CONTRACT_VIEW_ATTEMPTS = int(os.environ.get("EVE_MAX_GAME_CONTRACT_VIEW_ATTEMPTS", "3"))
GAME_READY_STABLE_SECONDS = float(os.environ.get("EVE_GAME_READY_STABLE_SECONDS", "3"))
PAUSE_AFTER_DISABLE_3D_RENDERING = float(os.environ.get("EVE_PAUSE_AFTER_DISABLE_3D_RENDERING", "1.5"))
DISABLE_3D_RENDERING_ON_GAME_START = os.environ.get("EVE_DISABLE_3D_RENDERING_ON_GAME_START", "1").lower() not in {"0", "false", "no"}
DISABLE_3D_RENDERING_ATTEMPTS = int(os.environ.get("EVE_DISABLE_3D_RENDERING_ATTEMPTS", "2"))
DISABLE_3D_RENDERING_MIN_MEAN_DIFF = float(os.environ.get("EVE_DISABLE_3D_RENDERING_MIN_MEAN_DIFF", "4.0"))
REQUIRE_3D_RENDERING_TOGGLE_CONFIRMATION = os.environ.get("EVE_REQUIRE_3D_RENDERING_TOGGLE_CONFIRMATION", "1").lower() not in {"0", "false", "no"}
LAUNCHER_FULLSCREEN_ON_START = os.environ.get("EVE_LAUNCHER_FULLSCREEN_ON_START", "1").lower() not in {"0", "false", "no"}
LAUNCHER_READY_STABLE_SECONDS = float(os.environ.get("EVE_LAUNCHER_READY_STABLE_SECONDS", "3"))
LAUNCHER_FULLSCREEN_MIN_MEAN_DIFF = float(os.environ.get("EVE_LAUNCHER_FULLSCREEN_MIN_MEAN_DIFF", "4.0"))
TIMEOUT_LAUNCHER_AFTER_F11 = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_AFTER_F11", "20"))
LAUNCHER_ACTION_RETRIES = int(os.environ.get("EVE_LAUNCHER_ACTION_RETRIES", "3"))
LAUNCHER_START_COMMAND_ATTEMPTS = int(os.environ.get("EVE_LAUNCHER_START_COMMAND_ATTEMPTS", "2"))
LAUNCHER_FOCUS_ATTEMPTS = int(os.environ.get("EVE_LAUNCHER_FOCUS_ATTEMPTS", "3"))
LAUNCHER_WINDOW_TITLE_PATTERNS = env_list("EVE_LAUNCHER_WINDOW_TITLE_PATTERNS", "eve launcher,eve online")
LAUNCHER_WINDOW_APP_ID_PATTERNS = env_list("EVE_LAUNCHER_WINDOW_APP_ID_PATTERNS", "evelauncher,eve,steam")
LAUNCHER_WINDOW_IGNORE_PATTERNS = env_list("EVE_LAUNCHER_WINDOW_IGNORE_PATTERNS", "tray")
TIMEOUT_LOCATE_CALDARI_FACTION = 20
TIMEOUT_LOCATE_NAME_BUTTON = 15
TIMEOUT_LOCATE_ADD_ACCOUNT_BTN = 25
TIMEOUT_LOCATE_ADD_ACCOUNT_BTN_AFTER_UNBUG = 20
TIMEOUT_LOCATE_SIGN_IN_BTN = 20
TIMEOUT_LOCATE_PLAY_BTN = 30

# --- Настройки для ЛАУНЧЕРА ---
LAUNCHER_ADD_ACCOUNT_BUTTON_IMG = 'screens/launcher_add_account_button.png'
LAUNCHER_USERNAME_FIELD_IMG = 'screens/launcher_username_field.png'
LAUNCHER_USERNAME_LABEL_IMG = 'screens/launcher_username_label.png'
LAUNCHER_PASSWORD_FIELD_IMG = 'screens/launcher_password_field.png'
LAUNCHER_PASSWORD_LABEL_IMG = 'screens/launcher_password_label.png'
LAUNCHER_SIGN_IN_BUTTON_IMG = 'screens/launcher_sign_in_button.png'
LAUNCHER_PLAY_BUTTON_IMG = 'screens/lancher_play_now_button.png'
LAUNCHER_ACCOUNT_SETTINGS_IMG = 'screens/launcher_account_settings_button.png'
LAUNCHER_CLIENT_RUNNING_STATUS_IMG = 'screens/launcher_button_status_client_is_running.png'
LAUNCHER_EMAIL_VERIFICATION_CODE_FIELD_IMG = 'screens/launcher_email_verification_code_field.png'
LAUNCHER_EMAIL_VERIFICATION_CONTINUE_IMG = 'screens/launcher_email_verification_continue_button.png'
LAUNCHER_REMOVE_ACCOUNT_BUTTON_IMG = 'screens/launcher_remove_account_button.png'
LAUNCHER_CONFIRM_REMOVE_BUTTON_IMG = 'screens/launcher_remove_account_button_2.png'
LAUNCHER_FULLSCREEN_IMG = 'screens/launcher_fullscreen.png'
LAUNCHER_FULLSCREEN_READY_STATUS_IMG = 'screens/launcher_fullscreen_ready_status.png'
LAUNCHER_FULLSCREEN_ACCOUNT_HEADER_IMG = 'screens/launcher_fullscreen_account_header.png'
GAME_ALPHA_STATUS_DOWNGRADE_EVENT_IMG = 'screens/game_alpa_status_downgrade_event.png'
GAME_ALPHA_STATUS_CLOSE_BUTTON_IMG = 'screens/game_alpha_status_close_button.png'
GAME_NEW_EVENT_IMG = 'screens/game_new_event.png'
GAME_NEW_EVENT_CLOSE_BUTTON_IMG = 'screens/game_new_event_close_button.png'
GAME_OMEGA_OFFER_IMG = 'screens/game_7_days_omega_offer_in_store_2.png'
GAME_OMEGA_FREE_BUTTON_IMG = 'screens/game_7_days_omega_offer_in_store_3(free button).png'
GAME_QUIT_GAME_BUTTON_IMG = 'screens/game_quit_game_button.png'
GAME_YES_BUTTON_AFTER_QUIT_IMG = 'screens/game_yes_button_after_quit.png'
GAME_REWARD_POPUP_TITLE_IMG = 'screens/game_reward_popup_title.png'
GAME_UNDOCK_BUTTON_IMG = 'screens/game_undock_button.png'
GAME_BOTTOM_NEOCOM_INDICATOR_IMG = 'screens/game_bottom_neocom_indicator.png'
GAME_TOP_LEFT_STATUS_INDICATOR_IMG = 'screens/game_top_left_status_indicator.png'
GAME_FINANCE_BUTTON_IMG = 'screens/game_finance_button.png'
GAME_CONTRACTS_BUTTON_IMG = 'screens/game_contracts_button.png'
GAME_MY_CONTRACTS_BUTTON_IMG = 'screens/game_my_contracts_button.png'
GAME_CONTRACT_NAME_BUTTON_IMG = 'screens/game_contract_name_button.png'
GAME_CONTRACT_ACCEPT_BUTTON_IMG = 'screens/game_contract_accept_button.png'
GAME_CONTRACT_YES_BUTTON_IMG = 'screens/game_contract_yes_button.png'
GAME_CONTRACT_CLOSE_BUTTON_IMG = 'screens/game_contract_close_button.png'
GAME_CLOSE_X_IMG = 'screens/x.png'
GAME_INVENTORY_ICON_IMG = 'screens/game_inventory_icon.png'
GAME_JITA4_IMG = 'screens/game_jita4.png'
GAME_SKILL_EXTRACTOR_IMG = 'screens/game_skill_extractor.png'
GAME_ACTIVATE_SKILL_EXTRACTOR_IMG = 'screens/game_activate_skill_extractor.png'
GAME_NOT_ENOUGH_SKILL_POINTS_ALERT_IMG = 'screens/game_not_enough_skill_points_alert.png'
IMAGE_ONLY_UI = os.environ.get("EVE_IMAGE_ONLY_UI", "1").lower() not in {"0", "false", "no"}
IMAGE_MATCH_DIAGNOSTICS = os.environ.get("EVE_IMAGE_MATCH_DIAGNOSTICS", "0").lower() not in {"0", "false", "no"}
GAME_PROCESS_PATTERNS = [
    pattern.strip().lower()
    for pattern in os.environ.get("EVE_GAME_PROCESS_PATTERNS", "exefile.exe").split(",")
    if pattern.strip()
]

EVE_ACCOUNT_USERNAME_PREFIX = os.environ.get("EVE_ACCOUNT_USERNAME_PREFIX", "my.eve.online.")
EVE_ACCOUNT_PASSWORD = os.environ.get("EVE_ACCOUNT_PASSWORD")
END_ACCOUNT_RANGE_FIXED = int(os.environ.get("EVE_END_ACCOUNT", "2000"))
MAX_LAUNCHER_RESTART_ATTEMPTS = 2

UNBUG_CLICK1_X, UNBUG_CLICK1_Y = 51, 180
UNBUG_CLICK2_X, UNBUG_CLICK2_Y = 53, 89

# --- Настройки для ДЕЙСТВИЙ В ИГРЕ ---
CC_CALDARI_FACTION_IMGS = ['caldari_faction_1.png', 'caldari_faction_2.png', 'caldari_faction_3.png', 'caldari_faction_4.png']
CC_SELECT_ORIGIN_CLICK_X, CC_SELECT_ORIGIN_CLICK_Y = 1284, 1334
CC_SELECT_RACE_CLICK_X, CC_SELECT_RACE_CLICK_Y = 1378, 685
CC_NAME_BUTTON = 'name.png'
CC_EDIT_APPEARANCE_X, CC_EDIT_APPEARANCE_Y = 1274, 1330
CC_NEXT_BUTTON_X, CC_NEXT_BUTTON_Y = 2486, 1391
CC_ENTER_GAME_BUTTON_X, CC_ENTER_GAME_BUTTON_Y = 2455, 1395
CC_SKIP_TUTORIAL_BUTTON_X, CC_SKIP_TUTORIAL_BUTTON_Y = 1008, 1396
NEW_ACC_SKILLS_OPEN_X, NEW_ACC_SKILLS_OPEN_Y = 19, 116
NEW_ACC_SKILLS_PERSONAL_X, NEW_ACC_SKILLS_PERSONAL_Y = 953, 132
NEW_ACC_SKILLS_CREATE_PLAN_X, NEW_ACC_SKILLS_CREATE_PLAN_Y = 827, 810
NEW_ACC_SKILLS_OPEN_MENU_X, NEW_ACC_SKILLS_OPEN_MENU_Y = 2167, 138
NEW_ACC_SKILLS_IMPORT_X, NEW_ACC_SKILLS_IMPORT_Y = 2204, 193
NEW_ACC_SKILLS_PLAN_NAME_X, NEW_ACC_SKILLS_PLAN_NAME_Y = 2258, 515
NEW_ACC_SKILLS_SAVE_PLAN_X, NEW_ACC_SKILLS_SAVE_PLAN_Y = 2443, 1389
NEW_ACC_SKILLS_SELECT_PLAN_X, NEW_ACC_SKILLS_SELECT_PLAN_Y = 248, 241
NEW_ACC_SKILLS_START_TRAINING_X, NEW_ACC_SKILLS_START_TRAINING_Y = 379, 1338
INGAME_ESC_MENU_LOGOUT_BUTTON_X = 1679
INGAME_ESC_MENU_LOGOUT_BUTTON_Y = 1391
CC_SUCCESS_VERIFICATION_IMG = 'character_creation_success_indicator.png'

# Глобальные переменные для состояния и сводки (event_logs УДАЛЕН)
capsulers_successfully_processed = 0
successfully_processed_usernames = []
launcher_restarts_count = 0
failed_accounts_details = []

consecutive_registration_failures = 0
total_registration_failures = 0

script_should_terminate = False
termination_reason_str = "Завершено штатно (достигнут конец диапазона)"
last_account_for_termination = None
last_failure_context_path = None
unhandled_exception_text = None


def log_event(message, important=False):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = ">>> " if important else "  " # Два пробела для обычного отступа
    log_message = f"{timestamp}:{prefix}{message}"
    
    print(log_message) # Вывод в консоль
    
    try:
        # Непрерывная запись в файл
        with open(resource_path(LOG_FILE_PATH), "a", encoding="utf-8") as log_file_writer:
            log_file_writer.write(log_message + "\n")
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА ЗАПИСИ ЛОГА В ФАЙЛ: {e} !!!")
        print(f"!!! Сообщение, которое не удалось записать: {log_message} !!!")


image_match_diagnostic_errors = set()


def calculate_image_match_score(image_filename):
    if not IMAGE_MATCH_DIAGNOSTICS:
        return None

    try:
        import cv2
        import numpy as np
        from PIL import Image

        template_path = resource_path(image_filename)
        if not template_path.exists():
            return {"status": "missing"}

        screenshot = pyautogui.screenshot().convert("RGB")
        template = Image.open(template_path).convert("RGB")
        screen_width, screen_height = screenshot.size
        template_width, template_height = template.size
        if template_width > screen_width or template_height > screen_height:
            return {
                "status": "too_large",
                "width": template_width,
                "height": template_height,
            }

        result = cv2.matchTemplate(
            np.array(screenshot),
            np.array(template),
            cv2.TM_CCOEFF_NORMED,
        )
        _, max_value, _, max_location = cv2.minMaxLoc(result)
        return {
            "status": "ok",
            "score": float(max_value),
            "x": int(max_location[0]),
            "y": int(max_location[1]),
            "width": template_width,
            "height": template_height,
        }
    except Exception as exc:
        error_key = f"{type(exc).__name__}: {exc}"
        if error_key not in image_match_diagnostic_errors:
            image_match_diagnostic_errors.add(error_key)
            log_event(f"IMAGE_MATCH_DIAG_ERROR {error_key}")
        return None


def log_image_match_diagnostic(image_filename, description, confidence_level, phase):
    score_info = calculate_image_match_score(image_filename)
    if not score_info:
        return

    status = score_info.get("status")
    if status != "ok":
        log_event(
            "IMAGE_MATCH_DIAG "
            f"phase={phase} status={status} threshold={confidence_level * 100:.1f}% "
            f"template='{image_filename}' description='{description}'"
        )
        return

    log_event(
        "IMAGE_MATCH_DIAG "
        f"phase={phase} score={score_info['score'] * 100:.1f}% "
        f"threshold={confidence_level * 100:.1f}% "
        f"best=({score_info['x']},{score_info['y']}) "
        f"size={score_info['width']}x{score_info['height']} "
        f"template='{image_filename}' description='{description}'"
    )


def log_image_match_diagnostics_for_options(image_options, description, confidence_level, phase):
    if not IMAGE_MATCH_DIAGNOSTICS:
        return

    for image_filename, image_description in image_options:
        log_image_match_diagnostic(
            image_filename,
            f"{description}: {image_description}",
            confidence_level,
            phase,
        )


def save_runtime_evidence_image(image, label):
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    safe_label = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in label)
    evidence_dir = resource_path(FAILURE_CONTEXT_DIR)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    output_path = evidence_dir / f"evidence_{safe_label}_{timestamp}.png"
    image.save(output_path)
    log_event(f"Evidence screenshot сохранён: {output_path}")
    return output_path


def central_screen_crop(image):
    width, height = image.size
    return image.crop(
        (
            int(width * 0.20),
            int(height * 0.18),
            int(width * 0.82),
            int(height * 0.86),
        )
    )


def mean_abs_image_difference(before_image, after_image):
    from PIL import ImageChops, ImageStat

    before_crop = central_screen_crop(before_image.convert("RGB"))
    after_crop = central_screen_crop(after_image.convert("RGB"))
    if before_crop.size != after_crop.size:
        after_crop = after_crop.resize(before_crop.size)
    diff = ImageChops.difference(before_crop, after_crop)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) / len(stat.mean)


def press_ctrl_shift_f9():
    pyautogui.keyDown('ctrl')
    time.sleep(0.05)
    pyautogui.keyDown('shift')
    time.sleep(0.05)
    pyautogui.press('f9')
    time.sleep(0.05)
    pyautogui.keyUp('shift')
    time.sleep(0.05)
    pyautogui.keyUp('ctrl')


def read_log_tail(max_lines=220):
    log_path = resource_path(LOG_FILE_PATH)
    try:
        if not log_path.exists():
            return ""
        with open(log_path, "r", encoding="utf-8", errors="replace") as log_file_reader:
            lines = log_file_reader.readlines()
        return "".join(lines[-max_lines:])
    except Exception as exc:
        return f"<failed to read log tail: {type(exc).__name__}: {exc}>"


def write_failure_context(reason, account_number=None, exception_text=None, exit_code=1):
    global last_failure_context_path

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    failure_dir = resource_path(FAILURE_CONTEXT_DIR)
    failure_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = None
    screenshot_error = None
    try:
        screenshot = pyautogui.screenshot()
        screenshot_path = failure_dir / f"failure_screenshot_{timestamp}.png"
        screenshot.save(screenshot_path)
    except Exception as exc:
        screenshot_error = f"{type(exc).__name__}: {exc}"

    context_path = failure_dir / f"failure_context_{timestamp}.json"
    payload = {
        "timestamp": timestamp,
        "reason": reason,
        "exit_code": exit_code,
        "current_account_number": account_number,
        "last_account_for_termination": last_account_for_termination,
        "launcher_command": describe_launcher_command(),
        "platform": platform.platform(),
        "python": sys.version,
        "session": {
            "XDG_SESSION_TYPE": os.environ.get("XDG_SESSION_TYPE", ""),
            "DISPLAY": os.environ.get("DISPLAY", ""),
            "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY", ""),
        },
        "log_file": str(resource_path(LOG_FILE_PATH)),
        "log_tail": read_log_tail(),
        "screenshot_path": str(screenshot_path) if screenshot_path else None,
        "screenshot_error": screenshot_error,
        "exception": exception_text,
        "next_start_account_hint": account_number or last_account_for_termination,
    }

    with open(context_path, "w", encoding="utf-8") as context_file:
        json.dump(payload, context_file, ensure_ascii=False, indent=2)

    last_failure_context_path = context_path
    log_event(f"Контекст сбоя сохранён для Codex CLI: {context_path}", important=True)
    if screenshot_path:
        log_event(f"Скриншот сбоя сохранён: {screenshot_path}")
    elif screenshot_error:
        log_event(f"Скриншот сбоя не сохранён: {screenshot_error}")
    return context_path


def determine_exit_code():
    if not script_should_terminate:
        return 0

    reason_lower = termination_reason_str.lower()
    if "ctrl+c" in reason_lower or "отмен" in reason_lower or "пользовател" in reason_lower:
        return 130
    if "завершено штатно" in reason_lower:
        return 0
    return 1


def require_runtime_secrets():
    global script_should_terminate, termination_reason_str

    missing = []
    if not EVE_ACCOUNT_PASSWORD:
        missing.append("EVE_ACCOUNT_PASSWORD")

    if missing:
        missing_vars = ", ".join(missing)
        script_should_terminate = True
        termination_reason_str = f"Не заданы обязательные переменные окружения: {missing_vars}. Заполните .env."
        raise SystemExit(termination_reason_str)

# --- Runtime helpers ---

def common_launcher_start_logic(is_initial_start=False, attempt_fullscreen=True):
    global launcher_restarts_count
    action = "Первоначальный запуск" if is_initial_start else "Перезапуск"
    launcher_command = get_launcher_command()
    command_attempts = max(1, LAUNCHER_START_COMMAND_ATTEMPTS if is_initial_start else 1)
    log_event(f"{action} лаунчера EVE Online командой: {describe_launcher_command()}", important=True)
    try:
        launcher_ready = False
        for command_attempt in range(1, command_attempts + 1):
            subprocess.Popen(launcher_command)
            log_event(f"Команда на запуск лаунчера отправлена (попытка {command_attempt}/{command_attempts}).")

            if wait_for_stable_launcher_ready(
                f"{action.lower()} лаунчера",
                timeout_seconds=TIMEOUT_LAUNCHER_READY,
            )[0]:
                launcher_ready = True
                break

            if command_attempt < command_attempts:
                log_event("Лаунчер не подтвердился после launch-команды. Пробуем найти окно и отправить команду ещё раз.", important=True)
                recover_existing_launcher_visibility("лаунчер перед повторной launch-командой")

        if not launcher_ready:
            return False

        if attempt_fullscreen and LAUNCHER_FULLSCREEN_ON_START:
            if not toggle_launcher_fullscreen_with_confirmation():
                return False
        elif attempt_fullscreen:
            log_event("F11 на старте лаунчера пропущен: EVE_LAUNCHER_FULLSCREEN_ON_START=0.")
        else:
            log_event("F11 пропущен для recovery/перезапуска лаунчера.")
        if not is_initial_start:
            launcher_restarts_count +=1
            log_event(f"Счетчик перезапусков лаунчера: {launcher_restarts_count}")
        return True
    except FileNotFoundError:
        log_event(f"ОШИБКА: Исполняемый файл лаунчера не найден: {launcher_command[0] if launcher_command else '<empty command>'}", important=True)
        return False
    except Exception as e:
        log_event(f"ОШИБКА при попытке '{action.lower()}' лаунчера: {e}", important=True)
        return False

def start_initial_launcher():
    return common_launcher_start_logic(is_initial_start=True, attempt_fullscreen=True)

def restart_eve_launcher():
    return common_launcher_start_logic(is_initial_start=False, attempt_fullscreen=False)

def try_unbug_launcher_clicks():
    if IMAGE_ONLY_UI:
        log_event("'Анти-баг' координатные клики отключены: включён image-only режим.")
        return

    log_event("Выполнение 'анти-баг' кликов в лаунчере...")
    human_click(UNBUG_CLICK1_X, UNBUG_CLICK1_Y)
    log_event(f"Анти-баг клик по ({UNBUG_CLICK1_X}, {UNBUG_CLICK1_Y}) выполнен.")
    time.sleep(PAUSE_BETWEEN_UNBUG_CLICKS)
    human_click(UNBUG_CLICK2_X, UNBUG_CLICK2_Y)
    log_event(f"Анти-баг клик по ({UNBUG_CLICK2_X}, {UNBUG_CLICK2_Y}) выполнен.")
    time.sleep(PAUSE_AFTER_UNBUG_CLICKS)
    log_event("'Анти-баг' клики завершены.")

def human_click(x, y, move_duration_base=0.15, move_duration_random=0.15, click_hold_duration=0.2):
    duration = move_duration_base + random.uniform(0, move_duration_random)
    pyautogui.moveTo(x, y, duration=duration)
    pyautogui.mouseDown(button='left')
    time.sleep(click_hold_duration)
    pyautogui.mouseUp(button='left')

def locate_image(image_filename, confidence_level=0.8):
    image_path = str(resource_path(image_filename))
    return pyautogui.locateCenterOnScreen(image_path, confidence=confidence_level)


def wait_for_any_image(image_options, description, timeout_seconds=30, confidence_level=0.8):
    log_event(f"Ожидаем состояние '{description}' по {len(image_options)} шаблонам, таймаут: {timeout_seconds} сек...")
    start_time = time.time()
    last_error = None
    while time.time() - start_time < timeout_seconds:
        for image_filename, image_description in image_options:
            try:
                location = locate_image(image_filename, confidence_level=confidence_level)
                if location:
                    log_image_match_diagnostic(image_filename, image_description, confidence_level, "found")
                    log_event(f"Состояние '{description}' подтверждено: найден '{image_description}' ({image_filename}).")
                    return image_filename, location
            except Exception as e:
                error_text = str(e).strip()
                if error_text and error_text != last_error:
                    log_event(f"ИСКЛЮЧЕНИЕ при ожидании '{description}': {error_text}")
                    last_error = error_text
                if "confidence" in error_text.lower() and "opencv" in error_text.lower():
                    log_event(">>> ВНИМАНИЕ: Для 'confidence' нужен OpenCV. Установи: pip install opencv-python")
        time.sleep(PAUSE_SHORT)

    log_image_match_diagnostics_for_options(image_options, description, confidence_level, "timeout")
    log_event(f"ОШИБКА: состояние '{description}' не подтверждено за {timeout_seconds} сек.", important=True)
    return None, None


def launcher_ready_templates():
    return [
        (LAUNCHER_ADD_ACCOUNT_BUTTON_IMG, "Add Account"),
        (LAUNCHER_PLAY_BUTTON_IMG, "Play Now"),
        (LAUNCHER_CLIENT_RUNNING_STATUS_IMG, "Client is running"),
        (LAUNCHER_FULLSCREEN_READY_STATUS_IMG, "Fullscreen launcher ready status"),
        (LAUNCHER_FULLSCREEN_ACCOUNT_HEADER_IMG, "Fullscreen Account Settings header"),
        (LAUNCHER_USERNAME_FIELD_IMG, "Username field"),
        (LAUNCHER_PASSWORD_FIELD_IMG, "Password field"),
        (LAUNCHER_SIGN_IN_BUTTON_IMG, "Sign In"),
    ]


def login_dialog_templates():
    return [
        (LAUNCHER_USERNAME_FIELD_IMG, "Username field"),
        (LAUNCHER_USERNAME_LABEL_IMG, "Username label"),
        (LAUNCHER_PASSWORD_FIELD_IMG, "Password field"),
        (LAUNCHER_PASSWORD_LABEL_IMG, "Password label"),
        (LAUNCHER_SIGN_IN_BUTTON_IMG, "Sign In"),
    ]


def play_ready_templates():
    return [
        (LAUNCHER_PLAY_BUTTON_IMG, "Play Now"),
    ]


def email_verification_templates():
    return [
        (LAUNCHER_EMAIL_VERIFICATION_CODE_FIELD_IMG, "Verification code field"),
        (LAUNCHER_EMAIL_VERIFICATION_CONTINUE_IMG, "Continue verification"),
    ]


def post_sign_in_templates():
    return [
        *play_ready_templates(),
        *email_verification_templates(),
    ]


def game_launch_confirmation_templates():
    return [
        (LAUNCHER_CLIENT_RUNNING_STATUS_IMG, "Client is running"),
    ]


def game_ready_templates():
    return [
        (GAME_UNDOCK_BUTTON_IMG, "Undock button"),
    ]


def game_popup_close_candidates():
    return [
        (
            GAME_NEW_EVENT_CLOSE_BUTTON_IMG,
            "New event close button",
            [(GAME_NEW_EVENT_IMG, "New event popup")],
        ),
        (
            GAME_ALPHA_STATUS_CLOSE_BUTTON_IMG,
            "Alpha status close button",
            [(GAME_ALPHA_STATUS_DOWNGRADE_EVENT_IMG, "Alpha status popup")],
        ),
    ]


def game_visible_templates():
    return [
        *game_ready_templates(),
        (GAME_QUIT_GAME_BUTTON_IMG, "Quit Game"),
    ]


def game_quit_confirmation_templates():
    return [
        (GAME_YES_BUTTON_AFTER_QUIT_IMG, "Quit Game confirmation Yes"),
        ("confirm_yes_button.png", "Generic confirmation Yes"),
    ]


def extractor_success_templates():
    return [
        (GAME_NOT_ENOUGH_SKILL_POINTS_ALERT_IMG, "Not enough skill points alert"),
    ]


def launcher_after_game_exit_templates():
    return [
        (LAUNCHER_PLAY_BUTTON_IMG, "Play Now"),
        (LAUNCHER_ADD_ACCOUNT_BUTTON_IMG, "Add Account"),
        (LAUNCHER_ACCOUNT_SETTINGS_IMG, "Account Settings"),
        (LAUNCHER_FULLSCREEN_READY_STATUS_IMG, "Fullscreen launcher ready status"),
        (LAUNCHER_FULLSCREEN_ACCOUNT_HEADER_IMG, "Fullscreen Account Settings header"),
    ]


def launcher_visibility_templates():
    unique_templates = []
    seen_filenames = set()
    for image_filename, image_description in [
        *launcher_ready_templates(),
        *launcher_after_game_exit_templates(),
    ]:
        if image_filename in seen_filenames:
            continue
        seen_filenames.add(image_filename)
        unique_templates.append((image_filename, image_description))
    return unique_templates


def wait_for_launcher_ready(context_description, timeout_seconds=TIMEOUT_LAUNCHER_READY):
    return wait_for_any_image(launcher_ready_templates(), context_description, timeout_seconds=timeout_seconds)[0] is not None


def wait_for_stable_launcher_ready(
    context_description,
    timeout_seconds=TIMEOUT_LAUNCHER_READY,
    stable_seconds=LAUNCHER_READY_STABLE_SECONDS,
    confidence_level=0.75,
):
    log_event(
        f"Ожидаем стабильное состояние лаунчера '{context_description}', "
        f"таймаут: {timeout_seconds} сек, stable: {stable_seconds:.1f} сек..."
    )
    start_time = time.time()
    stable_since = None
    stable_key = None
    stable_result = (None, None, None)
    logged_errors = set()

    while time.time() - start_time < timeout_seconds:
        image_filename, image_description, location = find_first_available_image(
            launcher_ready_templates(),
            confidence_level=confidence_level,
            logged_errors=logged_errors,
        )
        if image_filename:
            current_key = (image_filename, image_description)
            if current_key != stable_key:
                stable_key = current_key
                stable_since = time.time()
                stable_result = (image_filename, image_description, location)
                log_event(f"Лаунчер виден, проверяем стабильность: '{image_description}' ({image_filename}).")
            elif time.time() - stable_since >= stable_seconds:
                log_event(f"Лаунчер стабилен: '{image_description}' ({image_filename}).")
                return stable_result
        else:
            stable_since = None
            stable_key = None
            stable_result = (None, None, None)

        time.sleep(PAUSE_SHORT)

    log_image_match_diagnostics_for_options(
        launcher_ready_templates(),
        context_description,
        confidence_level,
        "stable_timeout",
    )
    log_event(f"ОШИБКА: стабильное состояние лаунчера '{context_description}' не подтверждено.", important=True)
    return None, None, None


def toggle_launcher_fullscreen_with_confirmation():
    log_event("Подготовка к F11: ждём стабильный лаунчер и фокусируем окно.", important=True)
    if not wait_for_stable_launcher_ready(
        "лаунчер перед F11",
        timeout_seconds=TIMEOUT_LAUNCHER_AFTER_F11,
    )[0]:
        return False

    if not recover_existing_launcher_visibility("лаунчер перед F11", force_focus=True):
        log_event("ОШИБКА: лаунчер перед F11 не удалось сфокусировать. F11 не нажимаем.", important=True)
        return False

    try:
        before_image = pyautogui.screenshot().convert("RGB")
    except Exception as exc:
        log_event(f"Не удалось сделать before screenshot перед F11: {type(exc).__name__}: {exc}", important=True)
        before_image = None

    if before_image is not None:
        save_runtime_evidence_image(before_image, "before_launcher_f11")

    log_event("Переключаем лаунчер в fullscreen через F11.", important=True)
    time.sleep(PAUSE_BEFORE_F11_ATTEMPT)
    pyautogui.press('f11')
    time.sleep(PAUSE_AFTER_F11_ATTEMPT)

    try:
        after_image = pyautogui.screenshot().convert("RGB")
    except Exception as exc:
        log_event(f"Не удалось сделать after screenshot после F11: {type(exc).__name__}: {exc}", important=True)
        after_image = None

    if after_image is not None:
        save_runtime_evidence_image(after_image, "after_launcher_f11")

    if before_image is not None and after_image is not None:
        mean_diff = mean_abs_image_difference(before_image, after_image)
        log_event(
            "LAUNCHER_F11_DIAG "
            f"mean_abs_diff={mean_diff:.2f} "
            f"required>={LAUNCHER_FULLSCREEN_MIN_MEAN_DIFF:.2f}"
        )
        if mean_diff < LAUNCHER_FULLSCREEN_MIN_MEAN_DIFF:
            log_event("ОШИБКА: F11 не подтверждён изменением экрана лаунчера. Продолжать небезопасно.", important=True)
            return False

    if not wait_for_stable_launcher_ready(
        "лаунчер после F11",
        timeout_seconds=TIMEOUT_LAUNCHER_AFTER_F11,
    )[0]:
        log_event("ОШИБКА: после F11 лаунчер не стабилизировался. Продолжать небезопасно.", important=True)
        return False

    log_event("F11 подтверждён: лаунчер снова стабилен после переключения.", important=True)
    return True


def wait_for_login_dialog_ready(timeout_seconds=TIMEOUT_LOGIN_DIALOG_READY):
    return wait_for_any_image(login_dialog_templates(), "диалог входа в аккаунт", timeout_seconds=timeout_seconds)[0] is not None


def wait_for_play_ready(timeout_seconds=TIMEOUT_AFTER_SIGN_IN_READY):
    return wait_for_any_image(play_ready_templates(), "кнопка Play после входа", timeout_seconds=timeout_seconds, confidence_level=0.75)[0] is not None


def wait_for_post_sign_in_state(timeout_seconds=TIMEOUT_AFTER_SIGN_IN_READY):
    image_filename, _ = wait_for_any_image(
        post_sign_in_templates(),
        "состояние после Sign In",
        timeout_seconds=timeout_seconds,
        confidence_level=0.75,
    )
    if not image_filename:
        return None
    if image_filename == LAUNCHER_PLAY_BUTTON_IMG:
        return "play"
    return "email_verification"


def wait_for_game_launch_confirmation(timeout_seconds=TIMEOUT_GAME_LAUNCH_VERIFICATION):
    return wait_for_any_image(game_launch_confirmation_templates(), "старт клиента игры в лаунчере", timeout_seconds=timeout_seconds, confidence_level=0.75)[0] is not None


def wait_for_game_closed_to_launcher(timeout_seconds=TIMEOUT_GAME_EXIT_TO_LAUNCHER):
    return wait_for_any_image(
        launcher_after_game_exit_templates(),
        "лаунчер после выхода из игры",
        timeout_seconds=timeout_seconds,
        confidence_level=0.75,
    )[0] is not None


def get_game_process_ids():
    if not GAME_PROCESS_PATTERNS:
        return set()

    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        log_event(f"Не удалось проверить процессы игры через ps: {type(exc).__name__}: {exc}")
        return set()

    if result.returncode != 0:
        error_text = result.stderr.strip()
        if error_text:
            log_event(f"ps вернул ошибку при проверке процессов игры: {error_text}")
        return set()

    current_pid = os.getpid()
    matched_pids = set()
    for line in result.stdout.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        if pid == current_pid:
            continue
        args_lower = parts[1].lower()
        if any(pattern in args_lower for pattern in GAME_PROCESS_PATTERNS):
            matched_pids.add(pid)
    return matched_pids


def get_niri_windows():
    if shutil.which("niri") is None:
        log_event("niri не найден в PATH, фокусировка существующего окна лаунчера недоступна.")
        return []

    try:
        result = subprocess.run(
            ["niri", "msg", "-j", "windows"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        log_event(f"Не удалось получить список окон niri: {type(exc).__name__}: {exc}")
        return []

    if result.returncode != 0:
        error_text = result.stderr.strip()
        log_event(f"niri msg -j windows вернул ошибку: {error_text or result.returncode}")
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        log_event(f"Не удалось разобрать JSON от niri: {exc}")
        return []

    if isinstance(data, list):
        windows = data
    elif isinstance(data, dict):
        windows = data.get("windows", [])
    else:
        windows = []
    return [window for window in windows if isinstance(window, dict)]


def get_window_text(window, *keys):
    for key in keys:
        value = window.get(key)
        if value:
            return str(value)
    return ""


def niri_window_summary(window):
    window_id = window.get("id", "?")
    app_id = get_window_text(window, "app_id", "app-id")
    title = get_window_text(window, "title")
    return f"id={window_id}, app_id='{app_id}', title='{title}'"


def rank_launcher_window(window):
    title = get_window_text(window, "title").lower()
    app_id = get_window_text(window, "app_id", "app-id").lower()
    combined = f"{title} {app_id}"

    if any(pattern in combined for pattern in LAUNCHER_WINDOW_IGNORE_PATTERNS):
        return 0

    score = 0
    for pattern in LAUNCHER_WINDOW_TITLE_PATTERNS:
        if pattern in title:
            score = max(score, 100)
        elif pattern in app_id:
            score = max(score, 80)

    for pattern in LAUNCHER_WINDOW_APP_ID_PATTERNS:
        if pattern not in combined:
            continue
        if pattern == "steam":
            score = max(score, 20)
        elif pattern == "eve":
            score = max(score, 60)
        else:
            score = max(score, 90)

    if score and window.get("is_focused"):
        score += 1
    return score


def rank_game_window(window):
    title = get_window_text(window, "title").lower()
    app_id = get_window_text(window, "app_id", "app-id").lower()
    combined = f"{title} {app_id}"

    if "launcher" in title or any(pattern in combined for pattern in LAUNCHER_WINDOW_IGNORE_PATTERNS):
        return 0

    score = 0
    if title.startswith("eve -"):
        score = max(score, 100)
    elif title.startswith("eve"):
        score = max(score, 80)

    if "steam_app_8500" in app_id and title:
        score = max(score, 70)

    if score and window.get("is_focused"):
        score += 1
    return score


def get_launcher_window_candidates():
    candidates = []
    for window in get_niri_windows():
        window_id = window.get("id")
        if window_id is None:
            continue
        score = rank_launcher_window(window)
        if score > 0:
            candidates.append((score, window))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def get_game_window_candidates():
    candidates = []
    for window in get_niri_windows():
        window_id = window.get("id")
        if window_id is None:
            continue
        score = rank_game_window(window)
        if score > 0:
            candidates.append((score, window))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def focus_niri_window(window_id):
    try:
        result = subprocess.run(
            ["niri", "msg", "action", "focus-window", "--id", str(window_id)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        log_event(f"Не удалось сфокусировать окно niri id={window_id}: {type(exc).__name__}: {exc}")
        return False

    if result.returncode != 0:
        error_text = result.stderr.strip()
        log_event(f"niri не сфокусировал окно id={window_id}: {error_text or result.returncode}")
        return False
    return True


def focus_existing_game_window(context_description, verify_timeout_seconds=TIMEOUT_LAUNCHER_FOCUS_VERIFY):
    candidates = get_game_window_candidates()
    if not candidates:
        log_event(f"{context_description}: niri не нашёл окно игры EVE.", important=True)
        return False

    candidate_text = "; ".join(
        f"{niri_window_summary(window)} score={score}"
        for score, window in candidates[:3]
    )
    log_event(f"{context_description}: niri кандидаты окна игры: {candidate_text}")

    for score, window in candidates[:3]:
        window_id = window.get("id")
        log_event(f"Фокусируем окно игры через niri: {niri_window_summary(window)} score={score}")
        if not focus_niri_window(window_id):
            continue
        time.sleep(PAUSE_MEDIUM)
        if wait_for_optional_image(
            game_ready_templates(),
            "игра после niri focus",
            timeout_seconds=verify_timeout_seconds,
            confidence_level=0.75,
        )[0]:
            log_event("Окно игры подтверждено после niri focus.", important=True)
            return True
        log_event("Окно игры сфокусировано, но игровая UI-проверка не подтвердилась.", important=True)

    return False


def wait_for_launcher_visible_optional(description, timeout_seconds=1):
    return wait_for_optional_image(
        launcher_visibility_templates(),
        description,
        timeout_seconds=timeout_seconds,
        confidence_level=0.75,
    )[0] is not None


def recover_existing_launcher_visibility(context_description, force_focus=False):
    if not force_focus and wait_for_launcher_visible_optional(context_description, timeout_seconds=1):
        return True

    if force_focus:
        log_event(
            f"{context_description}: требуется фокус окна лаунчера через niri перед действием.",
            important=True,
        )
    else:
        log_event(
            f"{context_description}: лаунчер не виден. Ищем уже открытое окно через niri, без повторного запуска Steam/EVE.",
            important=True,
        )

    for attempt in range(1, LAUNCHER_FOCUS_ATTEMPTS + 1):
        candidates = get_launcher_window_candidates()
        if not candidates:
            log_event("niri не нашёл подходящих окон лаунчера/EVE/Steam.")
            break

        top_candidates = candidates[:3]
        candidate_text = "; ".join(
            f"{niri_window_summary(window)} score={score}"
            for score, window in top_candidates
        )
        log_event(f"niri кандидаты окон для лаунчера, попытка {attempt}/{LAUNCHER_FOCUS_ATTEMPTS}: {candidate_text}")

        for score, window in top_candidates:
            window_id = window.get("id")
            log_event(f"Фокусируем окно через niri: {niri_window_summary(window)} score={score}")
            if not focus_niri_window(window_id):
                continue
            time.sleep(PAUSE_MEDIUM)
            if wait_for_launcher_visible_optional(
                "лаунчер после niri focus",
                timeout_seconds=TIMEOUT_LAUNCHER_FOCUS_VERIFY,
            ):
                log_event("Лаунчер подтверждён после фокусировки существующего окна niri.", important=True)
                return True

        time.sleep(PAUSE_MEDIUM)

    log_event(
        "Лаунчер не удалось подтвердить через существующие окна. Автозапуск через Steam здесь намеренно не выполняется.",
        important=True,
    )
    return False


def wait_for_game_ready_for_input(timeout_seconds=TIMEOUT_GAME_READY_FOR_INPUT):
    log_event(
        "Ожидаем загрузку игры по кнопке Undock, "
        f"таймаут: {timeout_seconds} сек..."
    )
    start_time = time.time()
    logged_errors = set()

    while time.time() - start_time < timeout_seconds:
        image_filename, image_description, _ = find_first_available_image(
            game_ready_templates(),
            confidence_level=0.75,
            logged_errors=logged_errors,
        )
        if image_filename:
            log_event(f"Готовность игры подтверждена: найден '{image_description}' ({image_filename}).")
            time.sleep(GAME_READY_STABLE_SECONDS)
            return True

        time.sleep(PAUSE_SHORT)

    log_event("ОШИБКА: кнопка Undock не найдена. Esc нажимать нельзя.", important=True)
    return False


def disable_3d_rendering_after_game_start():
    if not DISABLE_3D_RENDERING_ON_GAME_START:
        log_event("Отключение 3D-рендеринга пропущено: EVE_DISABLE_3D_RENDERING_ON_GAME_START=0.")
        return True

    for attempt in range(1, max(1, DISABLE_3D_RENDERING_ATTEMPTS) + 1):
        log_event(f"Отключаем 3D-рендеринг игры: Ctrl+Shift+F9, попытка {attempt}/{DISABLE_3D_RENDERING_ATTEMPTS}.", important=True)
        focus_existing_game_window("Перед Ctrl+Shift+F9")

        try:
            before_image = pyautogui.screenshot().convert("RGB")
        except Exception as exc:
            log_event(f"Не удалось сделать before screenshot перед Ctrl+Shift+F9: {type(exc).__name__}: {exc}", important=True)
            before_image = None

        if before_image is not None:
            save_runtime_evidence_image(before_image, f"before_disable_3d_attempt_{attempt}")

        press_ctrl_shift_f9()
        time.sleep(PAUSE_AFTER_DISABLE_3D_RENDERING)

        try:
            after_image = pyautogui.screenshot().convert("RGB")
        except Exception as exc:
            log_event(f"Не удалось сделать after screenshot после Ctrl+Shift+F9: {type(exc).__name__}: {exc}", important=True)
            after_image = None

        if after_image is not None:
            save_runtime_evidence_image(after_image, f"after_disable_3d_attempt_{attempt}")

        if not REQUIRE_3D_RENDERING_TOGGLE_CONFIRMATION:
            log_event("Подтверждение отключения 3D-рендеринга пропущено: EVE_REQUIRE_3D_RENDERING_TOGGLE_CONFIRMATION=0.")
            return True

        if before_image is None or after_image is None:
            continue

        mean_diff = mean_abs_image_difference(before_image, after_image)
        log_event(
            "3D_RENDER_TOGGLE_DIAG "
            f"attempt={attempt} mean_abs_diff={mean_diff:.2f} "
            f"required>={DISABLE_3D_RENDERING_MIN_MEAN_DIFF:.2f}"
        )
        if mean_diff >= DISABLE_3D_RENDERING_MIN_MEAN_DIFF:
            log_event("Отключение 3D-рендеринга подтверждено изменением экрана.", important=True)
            return True

        log_event("Ctrl+Shift+F9 не подтверждён изменением экрана. Повторяем.", important=True)

    log_event("ОШИБКА: отключение 3D-рендеринга не подтверждено. Внутриигровые UI-клики небезопасны.", important=True)
    return False


def wait_for_game_closed_confirmation(game_process_baseline, timeout_seconds=TIMEOUT_GAME_EXIT_TO_LAUNCHER):
    log_event(
        "Ожидаем подтверждение закрытия клиента игры: процесс игры завершился и лаунчер виден, "
        f"таймаут: {timeout_seconds} сек..."
    )
    start_time = time.time()
    logged_errors = set()
    last_status_log_at = 0

    while time.time() - start_time < timeout_seconds:
        launcher_image, launcher_description, _ = find_first_available_image(
            launcher_after_game_exit_templates(),
            confidence_level=0.75,
            logged_errors=logged_errors,
        )
        current_processes = get_game_process_ids()
        new_processes = current_processes - game_process_baseline

        if not new_processes:
            if launcher_image:
                log_event(f"Выход из игры подтверждён: процесс игры завершился, лаунчер показывает '{launcher_description}'.", important=True)
                return True

            log_event("Процесс игры завершился, но лаунчер не виден. Пробуем восстановить лаунчер перед удалением аккаунта.", important=True)
            if recover_existing_launcher_visibility("лаунчер после закрытия игры"):
                log_event("Лаунчер найден/сфокусирован после закрытия игры.", important=True)
                return True
            log_event("Лаунчер не удалось восстановить после закрытия игры.", important=True)
            return False

        if time.time() - last_status_log_at >= 8:
            status_parts = []
            if new_processes:
                status_parts.append(f"есть процесс игры PID {sorted(new_processes)}")
            if not launcher_image:
                status_parts.append("лаунчер не подтверждён")
            if status_parts:
                log_event("Игра ещё не считается закрытой: " + "; ".join(status_parts) + ".")
            last_status_log_at = time.time()

        time.sleep(PAUSE_SHORT)

    log_event("ОШИБКА: закрытие игры не подтверждено. Удаление аккаунта из лаунчера запрещено.", important=True)
    return False


def click_on_image(image_filename, description, confidence_level=0.8, timeout_seconds=10):
    log_event(f"Ищем '{description}' (файл: {image_filename}, таймаут: {timeout_seconds} сек)...")
    image_path = str(resource_path(image_filename))
    start_time = time.time()
    last_error = None
    while time.time() - start_time < timeout_seconds:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence_level)
            if location:
                log_image_match_diagnostic(image_filename, description, confidence_level, "found")
                human_click(location.x, location.y)
                log_event(f"Клик по '{description}' выполнен.")
                return True
            else:
                time.sleep(PAUSE_SHORT)
        except Exception as e:
            error_text = str(e).strip()
            if error_text and error_text != last_error:
                log_event(f"ИСКЛЮЧЕНИЕ при поиске/клике '{description}': {error_text}")
                last_error = error_text
            if "confidence" in error_text.lower() and "opencv" in error_text.lower():
                log_event(">>> ВНИМАНИЕ: Для 'confidence' нужен OpenCV. Установи: pip install opencv-python")
            time.sleep(PAUSE_SHORT)
    log_image_match_diagnostic(image_filename, description, confidence_level, "timeout")
    log_event(f"ОШИБКА: '{description}' ({image_filename}) не найдено на экране.", important=True)
    return False


def click_on_image_custom(
    image_filename,
    description,
    confidence_level=0.8,
    timeout_seconds=10,
    button="left",
    clicks=1,
    interval=0.1,
):
    log_event(
        f"Ищем '{description}' для {button}-click x{clicks} "
        f"(файл: {image_filename}, таймаут: {timeout_seconds} сек)..."
    )
    image_path = str(resource_path(image_filename))
    start_time = time.time()
    last_error = None
    while time.time() - start_time < timeout_seconds:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence_level)
            if location:
                log_image_match_diagnostic(image_filename, description, confidence_level, "found")
                pyautogui.moveTo(location.x, location.y, duration=0.12 + random.uniform(0, 0.12))
                pyautogui.click(location.x, location.y, clicks=clicks, interval=interval, button=button)
                log_event(f"{button}-click x{clicks} по '{description}' выполнен.")
                return True
            time.sleep(PAUSE_SHORT)
        except Exception as e:
            error_text = str(e).strip()
            if error_text and error_text != last_error:
                log_event(f"ИСКЛЮЧЕНИЕ при кастомном клике '{description}': {error_text}")
                last_error = error_text
            if "confidence" in error_text.lower() and "opencv" in error_text.lower():
                log_event(">>> ВНИМАНИЕ: Для 'confidence' нужен OpenCV. Установи: pip install opencv-python")
            time.sleep(PAUSE_SHORT)

    log_image_match_diagnostic(image_filename, description, confidence_level, "timeout")
    log_event(f"ОШИБКА: '{description}' ({image_filename}) не найдено для {button}-click x{clicks}.", important=True)
    return False


def click_screen_location_custom(location, description, button="left", clicks=1, interval=0.1):
    pyautogui.moveTo(location.x, location.y, duration=0.12 + random.uniform(0, 0.12))
    pyautogui.click(location.x, location.y, clicks=clicks, interval=interval, button=button)
    log_event(f"{button}-click x{clicks} по '{description}' выполнен в ({location.x}, {location.y}).")
    return True


def find_image(image_filename, description, confidence_level=0.8, timeout_seconds=10):
    log_event(f"Проверяем наличие '{description}' (файл: {image_filename}, таймаут: {timeout_seconds} сек)...")
    image_path = str(resource_path(image_filename))
    start_time = time.time()
    last_error = None
    while time.time() - start_time < timeout_seconds:
        try:
            if pyautogui.locateOnScreen(image_path, confidence=confidence_level):
                log_image_match_diagnostic(image_filename, description, confidence_level, "found")
                log_event(f"'{description}' найдено на экране.")
                return True
            else:
                time.sleep(PAUSE_SHORT)
        except Exception as e:
            error_text = str(e).strip()
            if error_text and error_text != last_error:
                log_event(f"ИСКЛЮЧЕНИЕ при поиске '{description}': {error_text}")
                last_error = error_text
            if "confidence" in error_text.lower() and "opencv" in error_text.lower():
                log_event(">>> ВНИМАНИЕ: Для 'confidence' нужен OpenCV. Установи: pip install opencv-python")
            time.sleep(PAUSE_SHORT)
    log_image_match_diagnostic(image_filename, description, confidence_level, "timeout")
    log_event(f"ОШИБКА ПРОВЕРКИ: '{description}' ({image_filename}) не найдено на экране.", important=True)
    return False


def wait_for_image_to_disappear(image_filename, description, confidence_level=0.8, timeout_seconds=10):
    log_event(f"Ожидаем исчезновение '{description}' (файл: {image_filename}, таймаут: {timeout_seconds} сек)...")
    start_time = time.time()
    last_error = None
    while time.time() - start_time < timeout_seconds:
        try:
            if not locate_image(image_filename, confidence_level=confidence_level):
                log_event(f"'{description}' больше не найдено на экране.")
                return True
        except Exception as e:
            if isinstance(e, pyautogui.ImageNotFoundException) or "could not locate" in str(e).lower():
                log_event(f"'{description}' больше не найдено на экране.")
                return True
            error_text = str(e).strip()
            if error_text and error_text != last_error:
                log_event(f"ИСКЛЮЧЕНИЕ при ожидании исчезновения '{description}': {error_text}")
                last_error = error_text
            if "confidence" in error_text.lower() and "opencv" in error_text.lower():
                log_event(">>> ВНИМАНИЕ: Для 'confidence' нужен OpenCV. Установи: pip install opencv-python")
        time.sleep(PAUSE_SHORT)
    log_event(f"ОШИБКА ПРОВЕРКИ: '{description}' не исчезло за {timeout_seconds} сек.", important=True)
    return False


def click_on_first_found_image(image_filenames_list, description, confidence_level=0.8, timeout_seconds=10):
    log_event(f"Ищем '{description}' (вариантов: {len(image_filenames_list)}, таймаут: {timeout_seconds} сек)...")
    start_time = time.time()
    attempt_interval = PAUSE_SHORT
    while time.time() - start_time < timeout_seconds:
        for image_filename in image_filenames_list:
            image_path = str(resource_path(image_filename))
            try:
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence_level)
                if location:
                    log_image_match_diagnostic(image_filename, description, confidence_level, "found")
                    human_click(location.x, location.y)
                    log_event(f"Клик по '{description}' (используя '{image_filename}') выполнен.")
                    return True
            except Exception as e:
                log_event(f"ИСКЛЮЧЕНИЕ при поиске '{image_filename}' для '{description}': {e}")
        time.sleep(attempt_interval)
    log_image_match_diagnostics_for_options(
        [(image_filename, image_filename) for image_filename in image_filenames_list],
        description,
        confidence_level,
        "timeout",
    )
    log_event(f"ОШИБКА: Ни один из вариантов для '{description}' не найден.", important=True)
    return False


def click_image_until_state(
    image_filename,
    description,
    success_templates,
    success_description,
    confidence_level=0.8,
    click_timeout_seconds=10,
    verify_timeout_seconds=5,
    attempts=LAUNCHER_ACTION_RETRIES,
):
    for attempt in range(1, attempts + 1):
        log_event(f"Попытка {attempt}/{attempts}: {description}.")
        if not click_on_image(
            image_filename,
            description,
            confidence_level=confidence_level,
            timeout_seconds=click_timeout_seconds,
        ):
            continue

        time.sleep(PAUSE_MEDIUM)
        found_image, found_description, _ = wait_for_optional_image(
            success_templates,
            success_description,
            timeout_seconds=verify_timeout_seconds,
            confidence_level=confidence_level,
        )
        if found_image:
            log_event(f"Post-click проверка '{description}' успешна: найдено '{found_description}' ({found_image}).")
            return True

        log_event(f"Post-click проверка '{description}' не подтвердила состояние '{success_description}'. Повторяем.", important=True)

    log_event(f"ОШИБКА: '{description}' не привело к состоянию '{success_description}' после {attempts} попыток.", important=True)
    return False


def click_image_until_disappears(
    image_filename,
    description,
    confidence_level=0.8,
    click_timeout_seconds=10,
    disappear_timeout_seconds=10,
    attempts=LAUNCHER_ACTION_RETRIES,
):
    clicked_at_least_once = False
    for attempt in range(1, attempts + 1):
        log_event(f"Попытка {attempt}/{attempts}: {description}.")
        if clicked_at_least_once and wait_for_image_to_disappear(
            image_filename,
            description,
            confidence_level=confidence_level,
            timeout_seconds=1,
        ):
            log_event(f"'{description}' уже исчезло после предыдущего клика. Считаем действие подтверждённым.")
            return True

        if not click_on_image(
            image_filename,
            description,
            confidence_level=confidence_level,
            timeout_seconds=click_timeout_seconds,
        ):
            continue

        clicked_at_least_once = True
        time.sleep(PAUSE_MEDIUM)
        if wait_for_image_to_disappear(
            image_filename,
            description,
            confidence_level=confidence_level,
            timeout_seconds=disappear_timeout_seconds,
        ):
            return True

        log_event(f"Post-click проверка '{description}' не подтвердила исчезновение. Повторяем.", important=True)

    log_event(f"ОШИБКА: '{description}' не исчезло после {attempts} попыток.", important=True)
    return False


def find_first_available_image(image_options, confidence_level=0.8, logged_errors=None):
    for image_filename, image_description in image_options:
        try:
            location = locate_image(image_filename, confidence_level=confidence_level)
            if location:
                log_image_match_diagnostic(image_filename, image_description, confidence_level, "found")
                return image_filename, image_description, location
        except Exception as e:
            error_text = str(e).strip()
            if error_text and logged_errors is not None and error_text not in logged_errors:
                log_event(f"ИСКЛЮЧЕНИЕ при optional-поиске '{image_description}': {error_text}")
                logged_errors.add(error_text)
            if logged_errors is not None and "confidence" in error_text.lower() and "opencv" in error_text.lower():
                opencv_hint = "Для 'confidence' нужен OpenCV. Установи: pip install opencv-python"
                if opencv_hint not in logged_errors:
                    log_event(f">>> ВНИМАНИЕ: {opencv_hint}")
                    logged_errors.add(opencv_hint)
    return None, None, None


def wait_for_optional_image(image_options, description, timeout_seconds=5, confidence_level=0.8):
    log_event(f"Проверяем optional-состояние '{description}', таймаут: {timeout_seconds} сек...")
    start_time = time.time()
    logged_errors = set()
    while time.time() - start_time < timeout_seconds:
        image_filename, image_description, location = find_first_available_image(
            image_options,
            confidence_level=confidence_level,
            logged_errors=logged_errors,
        )
        if location:
            log_event(f"Optional-состояние '{description}' найдено: '{image_description}' ({image_filename}).")
            return image_filename, image_description, location
        time.sleep(PAUSE_SHORT)

    log_event(f"Optional-состояние '{description}' не найдено.")
    return None, None, None


def click_optional_image(image_filename, description, confidence_level=0.8, timeout_seconds=3):
    image_found, image_description, location = wait_for_optional_image(
        [(image_filename, description)],
        description,
        timeout_seconds=timeout_seconds,
        confidence_level=confidence_level,
    )
    if not image_found:
        return False

    human_click(location.x, location.y)
    log_event(f"Optional-клик по '{image_description}' выполнен.")
    return True


def close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_SCAN):
    log_event(f"Проверяем всплывающие игровые окна/event popup, таймаут: {timeout_seconds} сек...")
    deadline = time.time() + timeout_seconds
    closed_count = 0
    logged_errors = set()

    while time.time() < deadline and closed_count < MAX_GAME_POPUP_CLOSE_ATTEMPTS:
        image_filename = image_description = location = None
        for close_image, close_description, evidence_templates in game_popup_close_candidates():
            evidence_image, evidence_description, _ = find_first_available_image(
                evidence_templates,
                confidence_level=0.75,
                logged_errors=logged_errors,
            )
            if not evidence_image:
                continue

            image_filename, image_description, location = find_first_available_image(
                [(close_image, close_description)],
                confidence_level=0.75,
                logged_errors=logged_errors,
            )
            if location:
                log_event(f"Popup evidence найден: '{evidence_description}' ({evidence_image}).")
                break

        if not location:
            time.sleep(PAUSE_SHORT)
            continue

        human_click(location.x, location.y)
        closed_count += 1
        log_event(f"Закрыто игровое окно '{image_description}' ({image_filename}).")
        time.sleep(PAUSE_MEDIUM)
        deadline = max(deadline, time.time() + PAUSE_MEDIUM)

    if closed_count >= MAX_GAME_POPUP_CLOSE_ATTEMPTS:
        log_event(f"Достигнут лимит закрытия popup за один аккаунт: {MAX_GAME_POPUP_CLOSE_ATTEMPTS}.", important=True)

    log_event(f"Проверка всплывающих игровых окон завершена. Закрыто: {closed_count}.")
    return True


def open_game_left_menu_and_click_finance():
    for attempt in range(1, 3):
        focus_existing_game_window("Перед открытием левого меню игры")
        log_event(f"Открываем левое меню игры клавишей '\\', попытка {attempt}/2.")
        pyautogui.press('\\')
        time.sleep(PAUSE_MEDIUM)
        if click_on_image(
            GAME_FINANCE_BUTTON_IMG,
            "кнопка Finance в левом меню",
            confidence_level=0.75,
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        ):
            return True
        log_event("Finance не найден после нажатия '\\'. Пробуем переключить меню ещё раз.", important=True)
    return False


def open_my_contracts_and_find_contract_name():
    for attempt in range(1, MAX_GAME_CONTRACT_VIEW_ATTEMPTS + 1):
        log_event(f"Открываем My Contracts и ищем контракт, попытка {attempt}/{MAX_GAME_CONTRACT_VIEW_ATTEMPTS}.")

        if attempt > 1:
            click_optional_image(
                GAME_CONTRACTS_BUTTON_IMG,
                "Contracts перед повторным My Contracts",
                confidence_level=0.75,
                timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
            )
            time.sleep(PAUSE_MEDIUM)

        clicks = 2 if attempt > 1 else 1
        if not click_on_image_custom(
            GAME_MY_CONTRACTS_BUTTON_IMG,
            "My Contracts",
            confidence_level=0.75,
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
            button="left",
            clicks=clicks,
            interval=0.2,
        ):
            continue

        time.sleep(PAUSE_MEDIUM)

        _, contract_description, contract_location = wait_for_optional_image(
            [(GAME_CONTRACT_NAME_BUTTON_IMG, "Contract name")],
            "Contract name после My Contracts",
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
            confidence_level=0.75,
        )
        if contract_location:
            log_event(f"My Contracts сработал: найден '{contract_description}'.")
            return contract_location

        log_event("После клика My Contracts контракт не появился. Повторяем.", important=True)

    log_event("ОШИБКА: My Contracts не привёл к видимому Contract name.", important=True)
    return None


def perform_contract_and_extractor_flow(current_username):
    log_event(f"--- Начало contract/extractor flow для {current_username} ---", important=True)

    if not open_game_left_menu_and_click_finance():
        log_event("ОШИБКА: не удалось открыть Finance через левое меню игры.", important=True)
        return False

    if not click_image_until_state(
        GAME_CONTRACTS_BUTTON_IMG,
        "Contracts",
        [(GAME_MY_CONTRACTS_BUTTON_IMG, "My Contracts")],
        "My Contracts после клика Contracts",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=2,
    ):
        return False

    contract_location = open_my_contracts_and_find_contract_name()
    if not contract_location:
        return False
    if not click_screen_location_custom(
        contract_location,
        "Contract name",
        button="left",
        clicks=2,
        interval=0.2,
    ):
        return False

    if not click_on_image(
        GAME_CONTRACT_ACCEPT_BUTTON_IMG,
        "Accept contract",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    if not click_on_image(
        GAME_CONTRACT_YES_BUTTON_IMG,
        "Yes на подтверждении контракта",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    click_optional_image(
        GAME_CONTRACT_CLOSE_BUTTON_IMG,
        "закрыть окно контракта",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
    )
    click_optional_image(
        GAME_CLOSE_X_IMG,
        "закрыть optional X",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
    )

    if not click_on_image(
        GAME_INVENTORY_ICON_IMG,
        "Inventory",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    if not click_on_image(
        GAME_JITA4_IMG,
        "Jita 4 в inventory",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    if not click_on_image_custom(
        GAME_SKILL_EXTRACTOR_IMG,
        "Skill Extractor",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        button="right",
    ):
        return False

    if not click_on_image(
        GAME_ACTIVATE_SKILL_EXTRACTOR_IMG,
        "Activate Skill Extractor",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    alert_image, alert_description, _ = wait_for_optional_image(
        extractor_success_templates(),
        "alert Not enough skill points",
        timeout_seconds=TIMEOUT_GAME_REQUIRED_STATE,
        confidence_level=0.75,
    )
    if not alert_image:
        log_event("ОШИБКА: не найден alert Not enough skill points после активации extractor.", important=True)
        return False

    log_event(f"Contract/extractor flow успешен: найден '{alert_description}' ({alert_image}).", important=True)
    click_optional_image(
        GAME_CLOSE_X_IMG,
        "закрыть alert Not enough skill points перед выходом",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
    )
    return True


def quit_game_to_launcher(game_process_baseline):
    log_event("--- Начало выхода из игры через Esc + Quit Game ---", important=True)

    for attempt in range(1, MAX_GAME_QUIT_MENU_ATTEMPTS + 1):
        close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_QUICK_SCAN)
        log_event(f"Открываем Esc-меню игры, попытка {attempt}/{MAX_GAME_QUIT_MENU_ATTEMPTS}.")
        pyautogui.press('esc')
        time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)

        image_filename, image_description, location = wait_for_optional_image(
            [(GAME_QUIT_GAME_BUTTON_IMG, "Quit Game")],
            "кнопка Quit Game в Esc-меню",
            timeout_seconds=TIMEOUT_GAME_QUIT_MENU_READY,
            confidence_level=0.75,
        )
        if location:
            human_click(location.x, location.y)
            log_event(f"Клик по '{image_description}' выполнен ({image_filename}).")
            time.sleep(PAUSE_AFTER_QUIT_GAME_CLICK)
            confirm_image, confirm_description, confirm_location = wait_for_optional_image(
                game_quit_confirmation_templates(),
                "подтверждение выхода после Quit Game",
                confidence_level=0.75,
                timeout_seconds=TIMEOUT_OPTIONAL_CONFIRM_DIALOG,
            )
            if confirm_location:
                human_click(confirm_location.x, confirm_location.y)
                log_event(f"Клик по подтверждению выхода выполнен: '{confirm_description}' ({confirm_image}).")
            else:
                log_event("Подтверждение выхода после Quit Game не найдено; продолжаем проверку закрытия клиента.")
            if wait_for_game_closed_confirmation(game_process_baseline, timeout_seconds=TIMEOUT_GAME_EXIT_TO_LAUNCHER):
                return True
            log_event("После Quit Game закрытие клиента/восстановление лаунчера не подтвердилось. Останавливаемся без удаления аккаунта.", important=True)
            return False

        close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_QUICK_SCAN)

    log_event("ОШИБКА: кнопка Quit Game не найдена после Esc. Выход из игры не подтверждён.", important=True)
    return False


def process_logged_in_game_session(current_username, game_process_baseline):
    log_event(f"--- Начало игровой сессии для {current_username}: закрыть popup, выполнить contract/extractor flow и выйти ---", important=True)
    close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_SCAN)
    if not perform_contract_and_extractor_flow(current_username):
        log_event("Обязательный contract/extractor flow не подтверждён. Пробуем штатно выйти, но аккаунт удалять нельзя.", important=True)
        quit_game_to_launcher(game_process_baseline)
        return False

    if not quit_game_to_launcher(game_process_baseline):
        return False

    log_event(f"--- Игровая сессия для {current_username} закрыта штатно. ---", important=True)
    return True


def read_skills_from_file(filepath):
    try:
        with open(resource_path(filepath), 'r', encoding='utf-8') as f:
            skills_text = f.read()
        if skills_text:
            log_event(f"Навыки успешно загружены из файла: {filepath}")
            return skills_text
        else:
            log_event(f"ОШИБКА: Файл навыков {filepath} пуст.", important=True)
            return None
    except FileNotFoundError:
        log_event(f"ОШИБКА: Файл навыков не найден: {filepath}", important=True)
        return None
    except Exception as e:
        log_event(f"ОШИБКА чтения файла навыков '{filepath}': {e}", important=True)
        return None

def require_image_only_template(image_filename, description):
    if resource_path(image_filename).exists():
        return True
    log_event(
        f"IMAGE-ONLY BLOCKER: нет шаблона '{image_filename}' для действия '{description}'. "
        "Добавьте crop в screens/ и подключите его перед запуском этого шага.",
        important=True,
    )
    return False

def type_text_into_image_field(image_filename, description, text_value, interval=0.15, timeout_seconds=10):
    image_filenames = [image_filename] if isinstance(image_filename, str) else list(image_filename)
    if not click_on_first_found_image(image_filenames, description, timeout_seconds=timeout_seconds):
        return False
    time.sleep(PAUSE_SHORT)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(PAUSE_SHORT)
    pyautogui.typewrite(text_value, interval=interval)
    log_event(f"Текст для '{description}' введён.")
    return True


def complete_email_verification(current_username, requested_at_epoch):
    log_event(f"Для {current_username} появился экран email verification. Получаем код из Gmail...")
    gmail_service = get_gmail_service(allow_interactive_auth=False, logger=log_event)
    if not gmail_service:
        log_event("ОШИБКА: Gmail service недоступен, verification code получить нельзя.", important=True)
        return False

    code = find_latest_eve_verification_code(
        gmail_service,
        newer_than_epoch=max(0, requested_at_epoch - EMAIL_VERIFICATION_REQUEST_SKEW_SECONDS),
        timeout_seconds=TIMEOUT_EMAIL_VERIFICATION_CODE,
        poll_interval=EMAIL_VERIFICATION_POLL_SECONDS,
    )
    if not code:
        log_event(f"ОШИБКА: verification code для {current_username} не найден в Gmail.", important=True)
        return False

    log_event("Verification code найден в Gmail. Вводим код в лаунчер.")
    if not type_text_into_image_field(
        LAUNCHER_EMAIL_VERIFICATION_CODE_FIELD_IMG,
        "Поле Verification Code",
        code,
        interval=0.08,
        timeout_seconds=TIMEOUT_EMAIL_VERIFICATION_PAGE,
    ):
        log_event("ОШИБКА: поле Verification Code не найдено.", important=True)
        return False

    if not click_on_image(
        LAUNCHER_EMAIL_VERIFICATION_CONTINUE_IMG,
        "Кнопка 'Continue' после verification code",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_EMAIL_VERIFICATION_PAGE,
    ):
        log_event("ОШИБКА: кнопка Continue на экране verification не найдена.", important=True)
        return False

    return True


def ensure_launcher_ready_for_account_removal():
    if wait_for_launcher_visible_optional(
        "лаунчер перед удалением аккаунта",
        timeout_seconds=TIMEOUT_LAUNCHER_ACCOUNT_REMOVAL_READY,
    ):
        return True

    log_event("Лаунчер перед удалением аккаунта не подтверждён. Пробуем найти уже открытое окно.", important=True)
    return recover_existing_launcher_visibility("лаунчер перед удалением аккаунта")


def remove_account_from_launcher(current_username):
    if IMAGE_ONLY_UI:
        required_templates = [
            (LAUNCHER_ACCOUNT_SETTINGS_IMG, "Account Settings"),
            (LAUNCHER_REMOVE_ACCOUNT_BUTTON_IMG, "Remove Account"),
            (LAUNCHER_CONFIRM_REMOVE_BUTTON_IMG, "Confirm Remove Account"),
        ]
        missing = [
            f"{description}: {image_filename}"
            for image_filename, description in required_templates
            if not resource_path(image_filename).exists()
        ]
        if missing:
            for item in missing:
                log_event(f"IMAGE-ONLY BLOCKER: отсутствует шаблон {item}", important=True)
            return False

    if not ensure_launcher_ready_for_account_removal():
        log_event("ОШИБКА: лаунчер не готов для удаления аккаунта.", important=True)
        return False

    if not click_image_until_state(
        LAUNCHER_ACCOUNT_SETTINGS_IMG,
        "Account Settings",
        [(LAUNCHER_REMOVE_ACCOUNT_BUTTON_IMG, "Remove Account")],
        "меню Account Settings с Remove Account",
        confidence_level=0.75,
        click_timeout_seconds=10,
        verify_timeout_seconds=6,
    ):
        return False
    if not click_image_until_state(
        LAUNCHER_REMOVE_ACCOUNT_BUTTON_IMG,
        "Remove Account",
        [(LAUNCHER_CONFIRM_REMOVE_BUTTON_IMG, "Confirm Remove Account")],
        "подтверждение Remove Account",
        confidence_level=0.75,
        click_timeout_seconds=10,
        verify_timeout_seconds=6,
    ):
        return False
    if not click_image_until_disappears(
        LAUNCHER_CONFIRM_REMOVE_BUTTON_IMG,
        "Confirm Remove Account",
        confidence_level=0.75,
        click_timeout_seconds=10,
        disappear_timeout_seconds=15,
    ):
        return False
    log_event(f"Аккаунт {current_username} удален из лаунчера.")
    return True

def perform_character_creation_and_setup(chabiad_name_number, skills_data_for_plan):
    global script_should_terminate, termination_reason_str, last_account_for_termination
    log_event(f"--- Начало создания персонажа Chabiad {chabiad_name_number} ---", important=True)
    if IMAGE_ONLY_UI:
        script_should_terminate = True
        last_account_for_termination = chabiad_name_number
        termination_reason_str = (
            "IMAGE-ONLY BLOCKER: старый in-game flow создания персонажа/skills всё ещё требует абсолютные координаты. "
            "Нужны актуальные crop-шаблоны для каждого действия в игре."
        )
        log_event(termination_reason_str, important=True)
        return False
    try:
        log_event("Этап 1: Выбор фракции, расы, внешности.")
        if not click_on_first_found_image(CC_CALDARI_FACTION_IMGS, "Значок фракции Калдари", timeout_seconds=TIMEOUT_LOCATE_CALDARI_FACTION): return False
        time.sleep(PAUSE_CC_AFTER_FACTION_SELECT)
        human_click(CC_SELECT_ORIGIN_CLICK_X, CC_SELECT_ORIGIN_CLICK_Y); log_event("Выбор происхождения выполнен."); time.sleep(PAUSE_CC_AFTER_ORIGIN_SELECT)
        human_click(CC_SELECT_RACE_CLICK_X, CC_SELECT_RACE_CLICK_Y); log_event("Выбор расы выполнен."); time.sleep(PAUSE_CC_AFTER_RACE_SELECT)
        human_click(CC_EDIT_APPEARANCE_X, CC_EDIT_APPEARANCE_Y); log_event("Переход к редактированию внешности."); time.sleep(PAUSE_CC_AFTER_EDIT_APPEARANCE)
        human_click(CC_NEXT_BUTTON_X, CC_NEXT_BUTTON_Y); log_event("Нажата кнопка 'Далее' после внешности."); time.sleep(PAUSE_CC_AFTER_NEXT_BUTTON)

        log_event("Этап 2: Ввод имени.")
        if not click_on_image(CC_NAME_BUTTON, "Поле для ввода имени", timeout_seconds=TIMEOUT_LOCATE_NAME_BUTTON): return False
        time.sleep(PAUSE_CC_AFTER_NAME_FIELD_CLICK)
        pyautogui.hotkey('ctrl', 'a'); time.sleep(PAUSE_SHORT)
        pyautogui.press('backspace'); time.sleep(PAUSE_MEDIUM)
        character_name = f"Chabiad {chabiad_name_number}"
        pyautogui.typewrite(character_name, interval=0.15); log_event(f"Имя '{character_name}' введено."); time.sleep(PAUSE_CC_AFTER_NAME_TYPE)
        human_click(CC_ENTER_GAME_BUTTON_X, CC_ENTER_GAME_BUTTON_Y); log_event("Нажата кнопка 'Войти в игру'."); time.sleep(PAUSE_CC_AFTER_ENTER_GAME_BUTTON)

        log_event("Этап 3: Пропуск обучения и загрузка в станцию.")
        pyautogui.press('space'); log_event("Нажат 'Пробел' для пропуска синематика."); time.sleep(PAUSE_CC_AFTER_SPACE_PRESS_IN_INTRO)
        pyautogui.press('esc'); log_event("Нажат 'Esc' для вызова меню."); time.sleep(PAUSE_CC_AFTER_ESC_IN_INTRO)
        human_click(CC_SKIP_TUTORIAL_BUTTON_X, CC_SKIP_TUTORIAL_BUTTON_Y); log_event("Нажата кнопка 'Пропустить обучение'."); time.sleep(PAUSE_CC_AFTER_SKIP_TUTORIAL_CLICK)
        pyautogui.press('enter'); log_event("Подтвержден пропуск обучения."); time.sleep(PAUSE_CC_AFTER_SKIP_TUTORIAL_CONFIRM)
        log_event(f"Ожидание загрузки в станцию ({PAUSE_CC_WAIT_FOR_STATION_LOAD} сек)..."); time.sleep(PAUSE_CC_WAIT_FOR_STATION_LOAD)

        log_event("--- Начало настройки плана навыков ---", important=True)
        human_click(NEW_ACC_SKILLS_OPEN_X, NEW_ACC_SKILLS_OPEN_Y); log_event("Открыто окно навыков."); time.sleep(PAUSE_SKILLS_AFTER_OPEN_WINDOW)
        human_click(NEW_ACC_SKILLS_PERSONAL_X, NEW_ACC_SKILLS_PERSONAL_Y); log_event("Переход на вкладку 'Личные'."); time.sleep(PAUSE_SKILLS_AFTER_PERSONAL_TAB)
        human_click(NEW_ACC_SKILLS_CREATE_PLAN_X, NEW_ACC_SKILLS_CREATE_PLAN_Y); log_event("Нажата кнопка 'Создать план'."); time.sleep(PAUSE_SKILLS_AFTER_CREATE_PLAN)
        human_click(NEW_ACC_SKILLS_OPEN_MENU_X, NEW_ACC_SKILLS_OPEN_MENU_Y); log_event("Открыто меню плана."); time.sleep(PAUSE_SKILLS_AFTER_OPEN_MENU)
        log_event("Копирование данных плана в буфер обмена..."); pyperclip.copy(skills_data_for_plan); time.sleep(PAUSE_SKILLS_AFTER_PASTE_IMPORT)
        human_click(NEW_ACC_SKILLS_IMPORT_X, NEW_ACC_SKILLS_IMPORT_Y); log_event("Нажата кнопка 'Импорт'."); time.sleep(PAUSE_SKILLS_AFTER_IMPORT_CLICK)
        human_click(NEW_ACC_SKILLS_PLAN_NAME_X, NEW_ACC_SKILLS_PLAN_NAME_Y); log_event("Клик по полю имени плана."); time.sleep(PAUSE_SKILLS_AFTER_PLAN_NAME_CLICK)
        pyautogui.typewrite("11", interval=0.15); log_event("Введено имя плана '11'."); time.sleep(PAUSE_SKILLS_AFTER_PLAN_NAME_TYPE)
        human_click(NEW_ACC_SKILLS_SAVE_PLAN_X, NEW_ACC_SKILLS_SAVE_PLAN_Y); log_event("План сохранен."); time.sleep(PAUSE_SKILLS_AFTER_SAVE_PLAN)
        human_click(NEW_ACC_SKILLS_SELECT_PLAN_X, NEW_ACC_SKILLS_SELECT_PLAN_Y); log_event("Выбран сохраненный план."); time.sleep(PAUSE_SKILLS_AFTER_SELECT_PLAN)
        human_click(NEW_ACC_SKILLS_START_TRAINING_X, NEW_ACC_SKILLS_START_TRAINING_Y); log_event("Нажата кнопка 'Начать освоение'."); time.sleep(PAUSE_SKILLS_AFTER_START_TRAINING)

        log_event("--- Проверка успешного старта изучения плана ---", important=True)
        time.sleep(PAUSE_BEFORE_SUCCESS_VERIFICATION)
        if not find_image(CC_SUCCESS_VERIFICATION_IMG, "Индикатор успешного старта изучения плана", timeout_seconds=PAUSE_SUCCESS_VERIFICATION_TIMEOUT):
            log_event(f"ОШИБКА ПРОВЕРКИ: Индикатор для Chabiad {chabiad_name_number} НЕ НАЙДЕН. Регистрация считается неуспешной.", important=True)
            log_event("Попытка аварийного выхода из игры...");
            pyautogui.press('esc'); time.sleep(PAUSE_SHORT)
            pyautogui.press('esc'); time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)
            human_click(INGAME_ESC_MENU_LOGOUT_BUTTON_X, INGAME_ESC_MENU_LOGOUT_BUTTON_Y); time.sleep(PAUSE_AFTER_LOGOUT_BUTTON_CLICK)
            pyautogui.press('enter')
            time.sleep(PAUSE_FOR_GAME_TO_CLOSE)
            return False

        log_event(f"Успешный старт изучения плана для Chabiad {chabiad_name_number} подтвержден.", important=True)

        log_event("--- Начало выхода из игры ---", important=True)
        pyautogui.press('esc'); time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)
        pyautogui.press('esc'); log_event("Двойное нажатие 'Esc' для закрытия всех окон."); time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)
        human_click(INGAME_ESC_MENU_LOGOUT_BUTTON_X, INGAME_ESC_MENU_LOGOUT_BUTTON_Y); log_event("Нажата кнопка 'Выйти из игры'."); time.sleep(PAUSE_AFTER_LOGOUT_BUTTON_CLICK)
        pyautogui.press('enter'); log_event("Подтвержден выход из игры.")
        log_event(f"Ожидание закрытия клиента игры ({PAUSE_FOR_GAME_TO_CLOSE} сек)..."); time.sleep(PAUSE_FOR_GAME_TO_CLOSE)
        log_event(f"--- Chabiad {chabiad_name_number}: Все игровые действия и выход завершены. ---", important=True)
        return True
    except Exception as e_ingame_main:
        log_event(f"КРИТИЧЕСКОЕ ИСКЛЮЧЕНИЕ во время создания/настройки Chabiad {chabiad_name_number}: {e_ingame_main}", important=True)
        try:
            log_event("Попытка аварийного выхода из игры после исключения...")
            pyautogui.press('esc'); time.sleep(PAUSE_SHORT)
            pyautogui.press('esc'); time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)
            human_click(INGAME_ESC_MENU_LOGOUT_BUTTON_X, INGAME_ESC_MENU_LOGOUT_BUTTON_Y); time.sleep(PAUSE_AFTER_LOGOUT_BUTTON_CLICK)
            pyautogui.press('enter')
            time.sleep(PAUSE_FOR_GAME_TO_CLOSE_EMERGENCY)
        except Exception as e_exit:
            log_event(f"Ошибка при аварийном выходе: {e_exit}")
        return False

def save_logs_summary(): # Переименована для ясности, что это только сводка
    global capsulers_successfully_processed, failed_accounts_details, launcher_restarts_count
    global script_should_terminate, termination_reason_str, last_account_for_termination, successfully_processed_usernames
    
    # Эта функция теперь ТОЛЬКО пишет итоговую сводку в конец файла логов.
    # Детальные логи уже пишутся функцией log_event()
    try:
        with open(resource_path(LOG_FILE_PATH), "a", encoding="utf-8") as log_file_writer:
            log_file_writer.write("\n\n--- Сводка по сессии ---\n") # Добавим пару пустых строк перед сводкой
            log_file_writer.write(f"Всего успешно обработано аккаунтов: {capsulers_successfully_processed} (из них имен в списке: {len(successfully_processed_usernames)})\n")
            if successfully_processed_usernames:
                log_file_writer.write("Успешно обработанные аккаунты (username):\n")
                for uname in successfully_processed_usernames:
                    log_file_writer.write(f"  - {uname}\n")
            else:
                log_file_writer.write("Успешно обработанных аккаунтов (по именам) нет.\n")

            if failed_accounts_details:
                log_file_writer.write("\nАккаунты с проблемами (номер и причина):\n")
                for acc_num, reason in failed_accounts_details:
                    log_file_writer.write(f"  - Аккаунт номер {acc_num} ({EVE_ACCOUNT_USERNAME_PREFIX}{acc_num}): {reason}\n")
            else:
                log_file_writer.write("Проблемных аккаунтов не зафиксировано.\n")
            
            log_file_writer.write(f"\nКоличество перезапусков лаунчера за сессию: {launcher_restarts_count}\n")

            if script_should_terminate:
                log_file_writer.write(f"\n--- Скрипт был остановлен ---\n")
                log_file_writer.write(f"Причина: {termination_reason_str}\n")
                if last_account_for_termination is not None:
                    log_file_writer.write(f"Последний обрабатываемый номер аккаунта: {last_account_for_termination} ({EVE_ACCOUNT_USERNAME_PREFIX}{last_account_for_termination})\n")
            else:
                log_file_writer.write(f"\n--- Сессия завершена: {termination_reason_str} ---\n")

            log_file_writer.write(f"--- Конец сводки и лога сессии от {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")
        
        print(f"Сводка сессии также добавлена в файл: {LOG_FILE_PATH}")
    except Exception as e:
        print(f"!!! КРИТИЧЕСКАЯ ОШИБКА СОХРАНЕНИЯ СВОДКИ ЛОГОВ: {e} !!!")

# --- Основной процесс ---
if __name__ == "__main__":
    current_account_number = 0 
    start_account_number = 0   
    
    # --- Начало новой сессии логирования ---
    # Записываем заголовок новой сессии в файл логов ПЕРЕД первым вызовом log_event
    try:
        with open(resource_path(LOG_FILE_PATH), "a", encoding="utf-8") as log_file_writer:
            # Добавляем несколько пустых строк, если файл уже существует, для лучшего разделения сессий
            log_file_writer.seek(0, 2) # Перемещаемся в конец файла
            if log_file_writer.tell() > 0: # Если файл не пустой
                log_file_writer.write("\n\n")
            log_file_writer.write(f"--- НОВАЯ СЕССИЯ от {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    except Exception as e:
        print(f"!!! НЕ УДАЛОСЬ ЗАПИСАТЬ ЗАГОЛОВОК НОВОЙ СЕССИИ В ЛОГ-ФАЙЛ: {e} !!!")
        # Продолжаем выполнение, но предупреждаем пользователя

    try:
        log_event("Запуск скрипта.", important=True)
        require_runtime_secrets()

        try:
            start_account_number_str = os.environ.get("EVE_START_ACCOUNT")
            if start_account_number_str:
                log_event(f"Начальный номер взят из EVE_START_ACCOUNT={start_account_number_str}.")
            else:
                start_account_number_str = pyautogui.prompt(
                    text='Введите НАЧАЛЬНЫЙ номер для аккаунта EVE (например, 31):',
                    title='Начальный номер', default='31'
                )
                if start_account_number_str is None:
                    script_should_terminate = True
                    termination_reason_str = "Запуск отменен пользователем при вводе номера."
                    raise SystemExit(termination_reason_str)
            start_account_number = int(start_account_number_str)
            if not (1 <= start_account_number <= END_ACCOUNT_RANGE_FIXED):
                script_should_terminate = True
                termination_reason_str = f"Начальный номер ({start_account_number}) вне диапазона [1-{END_ACCOUNT_RANGE_FIXED}]."
                raise SystemExit(termination_reason_str)
        except ValueError:
            script_should_terminate = True
            termination_reason_str = "Неверный формат начального номера. Введите целое число."
            raise SystemExit(termination_reason_str)
        except Exception as e_prompt: 
            script_should_terminate = True
            termination_reason_str = f"Ошибка при вводе начального номера: {e_prompt}"
            raise SystemExit(termination_reason_str)

        current_account_number = start_account_number
        log_event(f"--- Начинаем автоматическую обработку аккаунтов с номера {start_account_number} до {END_ACCOUNT_RANGE_FIXED} ---", important=True)

        if not start_initial_launcher():
            script_should_terminate = True
            termination_reason_str = "Не удалось выполнить первоначальный запуск лаунчера."
            last_account_for_termination = current_account_number 
            raise SystemExit(termination_reason_str)

        launcher_restart_attempts_for_current_acc = 0

        while current_account_number <= END_ACCOUNT_RANGE_FIXED:
            if script_should_terminate: break
            
            current_username = f"{EVE_ACCOUNT_USERNAME_PREFIX}{current_account_number}"
            log_event(f">>> Попытка обработки аккаунта: {current_username} (Номер {current_account_number}) <<<", important=True)
            game_launched_successfully = False
            account_processing_step_failed = False 

            log_event(f"Шаг 1: Добавление учетной записи {current_username} в лаунчер.")
            add_account_button_found = click_on_image(LAUNCHER_ADD_ACCOUNT_BUTTON_IMG, "Кнопка 'Добавить учётную запись'", timeout_seconds=TIMEOUT_LOCATE_ADD_ACCOUNT_BTN)
            if not add_account_button_found:
                log_event(f"Кнопка 'Добавить учётную запись' не найдена. Применяем 'анти-баг' клики.")
                try_unbug_launcher_clicks()
                add_account_button_found = click_on_image(LAUNCHER_ADD_ACCOUNT_BUTTON_IMG, "Кнопка 'Добавить учётную запись' (после анти-бага)", timeout_seconds=TIMEOUT_LOCATE_ADD_ACCOUNT_BTN_AFTER_UNBUG)

            if not add_account_button_found:
                log_event(f"ОШИБКА ЛАУНЧЕРА: Кнопка 'Добавить учётную запись' не найдена для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher():
                        launcher_restart_attempts_for_current_acc += 1
                        log_event(f"Лаунчер перезапущен. Попытка {launcher_restart_attempts_for_current_acc}/{MAX_LAUNCHER_RESTART_ATTEMPTS} для {current_username}.")
                        time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC)
                        continue 
                    else:
                        script_should_terminate = True; termination_reason_str = "Критическая ошибка: Перезапуск лаунчера не удался."; last_account_for_termination = current_account_number; break
                else:
                    script_should_terminate = True; termination_reason_str = "Исчерпаны попытки перезапуска лаунчера для кнопки 'Добавить уч. запись'."; last_account_for_termination = current_account_number; break
            if not wait_for_login_dialog_ready(timeout_seconds=TIMEOUT_LOGIN_DIALOG_READY):
                log_event(f"ОШИБКА ЛАУНЧЕРА: диалог входа не подтвердился для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher():
                        launcher_restart_attempts_for_current_acc += 1
                        continue
                    else:
                        script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после Login dialog fail."; last_account_for_termination = current_account_number; break
                else:
                    failed_accounts_details.append((current_account_number, "Launcher: login dialog not confirmed after retries")); account_processing_step_failed = True
            if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue

            log_event(f"Шаг 2: Ввод логина и пароля для {current_username}.")
            if not type_text_into_image_field([LAUNCHER_USERNAME_FIELD_IMG, LAUNCHER_USERNAME_LABEL_IMG], "Поле Username", current_username, timeout_seconds=TIMEOUT_LOCATE_SIGN_IN_BTN):
                log_event(f"ОШИБКА ЛАУНЧЕРА: поле Username не найдено для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else: script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после Username fail."; last_account_for_termination = current_account_number; break
                else:
                    failed_accounts_details.append((current_account_number, "Launcher: Username field not found after retries")); account_processing_step_failed = True
            if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue
            time.sleep(PAUSE_AFTER_USERNAME_TYPE)

            if not type_text_into_image_field([LAUNCHER_PASSWORD_FIELD_IMG, LAUNCHER_PASSWORD_LABEL_IMG], "Поле Password", EVE_ACCOUNT_PASSWORD, timeout_seconds=TIMEOUT_LOCATE_SIGN_IN_BTN):
                log_event(f"ОШИБКА ЛАУНЧЕРА: поле Password не найдено для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else: script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после Password fail."; last_account_for_termination = current_account_number; break
                else:
                    failed_accounts_details.append((current_account_number, "Launcher: Password field not found after retries")); account_processing_step_failed = True
            if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue
            time.sleep(PAUSE_AFTER_PASSWORD_TYPE)

            if not click_on_image(LAUNCHER_SIGN_IN_BUTTON_IMG, "Кнопка 'Sign In'", timeout_seconds=TIMEOUT_LOCATE_SIGN_IN_BTN):
                log_event(f"ОШИБКА ЛАУНЧЕРА: Кнопка 'Sign In' не найдена для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else: script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после 'Sign In' fail."; last_account_for_termination = current_account_number; break
                else: 
                    log_event(f"Пропускаем аккаунт {current_username} из-за ошибки 'Sign In'."); failed_accounts_details.append((current_account_number, "Launcher: 'Sign In' not found after retries")); account_processing_step_failed = True
            if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue 
            if script_should_terminate: break # Проверка после потенциального fail fast

            email_verification_requested_at = time.time()
            post_sign_in_state = wait_for_post_sign_in_state(timeout_seconds=TIMEOUT_AFTER_SIGN_IN_READY)
            if post_sign_in_state == "email_verification":
                if not complete_email_verification(current_username, email_verification_requested_at):
                    log_event(f"ОШИБКА ЛАУНЧЕРА: email verification не пройден для {current_username}.", important=True)
                    failed_accounts_details.append((current_account_number, "Launcher: email verification failed; Gmail/code unavailable"))
                    script_should_terminate = True
                    termination_reason_str = "Крит. ошибка: email verification не пройден. Дальше идти нельзя, нужен доступ к Gmail или свежий код."
                    last_account_for_termination = current_account_number
                    break
                if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue
                if not wait_for_play_ready(timeout_seconds=TIMEOUT_AFTER_SIGN_IN_READY):
                    log_event(f"ОШИБКА ЛАУНЧЕРА: кнопка Play не подтвердилась после email verification для {current_username}.", important=True)
                    failed_accounts_details.append((current_account_number, "Launcher: Play not confirmed after email verification"))
                    script_should_terminate = True
                    termination_reason_str = "Крит. ошибка: после email verification не подтвердился переход к Play."
                    last_account_for_termination = current_account_number
                    break
            elif post_sign_in_state != "play":
                log_event(f"ОШИБКА ЛАУНЧЕРА: после входа не подтвердились ни Play, ни email verification для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher():
                        launcher_restart_attempts_for_current_acc += 1
                        continue
                    else:
                        script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после ожидания post-sign-in state fail."; last_account_for_termination = current_account_number; break
                else:
                    failed_accounts_details.append((current_account_number, "Launcher: post-sign-in state not confirmed after retries")); account_processing_step_failed = True
            if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue

            log_event(f"Шаг 3: Запуск игры для {current_username}.")
            game_process_baseline = get_game_process_ids()
            if click_image_until_state(
                LAUNCHER_PLAY_BUTTON_IMG,
                "Кнопка 'Играть'",
                game_launch_confirmation_templates(),
                "статус Client is running после Play",
                confidence_level=0.75,
                click_timeout_seconds=TIMEOUT_LOCATE_PLAY_BTN,
                verify_timeout_seconds=TIMEOUT_GAME_LAUNCH_VERIFICATION,
                attempts=LAUNCHER_ACTION_RETRIES,
            ):
                log_event("Кнопка 'Играть' сработала. Ожидаем кнопку Undock перед Esc...")
                if wait_for_game_ready_for_input(timeout_seconds=TIMEOUT_GAME_READY_FOR_INPUT):
                    if disable_3d_rendering_after_game_start():
                        game_launched_successfully = True
                    else:
                        failed_accounts_details.append((current_account_number, "In-game: 3D rendering disable was not confirmed"))
                        account_processing_step_failed = True
                        script_should_terminate = True
                        termination_reason_str = "Крит. ошибка: отключение 3D-рендеринга не подтверждено. Внутриигровые UI-клики остановлены."
                        last_account_for_termination = current_account_number
                        quit_game_to_launcher(game_process_baseline)
                        break
                else:
                    log_event(f"ОШИБКА: игра не стала готова к вводу для {current_username}.", important=True)
                    if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                        if restart_eve_launcher():
                            launcher_restart_attempts_for_current_acc += 1
                            continue
                        else:
                            script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после неподтверждённой готовности игры."; last_account_for_termination = current_account_number; break
                    else:
                        failed_accounts_details.append((current_account_number, "In-game: readiness not confirmed after launch")); account_processing_step_failed = True
            else:
                log_event(f"ОШИБКА ЛАУНЧЕРА: Play не привёл к статусу Client is running для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else: script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после 'Play' fail."; last_account_for_termination = current_account_number; break
                else:
                    log_event(f"Пропускаем аккаунт {current_username} из-за ошибки 'Play'."); failed_accounts_details.append((current_account_number, "Launcher: Play did not lead to Client is running")); account_processing_step_failed = True
            if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue
            if script_should_terminate: break # Проверка после потенциального fail fast
            
            if game_launched_successfully:
                log_event(f"Шаг 4: Закрытие popup/event окон и выход из игры для {current_username}.")
                launcher_restart_attempts_for_current_acc = 0 
                if process_logged_in_game_session(current_username, game_process_baseline):
                    log_event(f"--- УСПЕХ: Игровая сессия для {current_username} закрыта. ---", important=True)
                    capsulers_successfully_processed += 1
                    successfully_processed_usernames.append(current_username)
                    consecutive_registration_failures = 0

                    log_event(f"Шаг 5: Удаление аккаунта {current_username} из лаунчера.")
                    time.sleep(PAUSE_BEFORE_ACCOUNT_DELETION_ACTIONS)
                    if not remove_account_from_launcher(current_username):
                        log_event(f"Удаление аккаунта {current_username} из лаунчера не выполнено в image-only режиме.", important=True)
                        failed_accounts_details.append((current_account_number, "Launcher: account removal was not confirmed by image templates"))
                        account_processing_step_failed = True
                        script_should_terminate = True
                        termination_reason_str = "Крит. ошибка: удаление аккаунта из лаунчера не подтверждено по image templates."
                        last_account_for_termination = current_account_number
                    if not account_processing_step_failed:
                        log_event(f"--- УСПЕХ ПОЛНЫЙ: Аккаунт {current_username} полностью обработан. ---", important=True)
                else:
                    log_event(f"--- НЕУДАЧА: не удалось штатно закрыть игровую сессию для {current_username}. ---", important=True)
                    failed_accounts_details.append((current_account_number, "In-game: contract/extractor flow or Quit Game failed"))
                    account_processing_step_failed = True 

                    script_should_terminate = True
                    termination_reason_str = "Крит. ошибка: обязательный in-game flow или выход через Esc + Quit Game не подтверждён. Удалять аккаунт из лаунчера нельзя."
                    last_account_for_termination = current_account_number
                    break
            else: 
                log_event(f"Игра не была запущена для {current_username}, внутриигровые шаги и удаление пропущены.")

            current_account_number += 1
            launcher_restart_attempts_for_current_acc = 0 
            if current_account_number <= END_ACCOUNT_RANGE_FIXED and not script_should_terminate:
                log_event(f"Пауза перед обработкой следующего аккаунта ({PAUSE_BETWEEN_ACCOUNTS_PROCESSING} секунд)...")
                time.sleep(PAUSE_BETWEEN_ACCOUNTS_PROCESSING)
            elif not script_should_terminate: 
                 termination_reason_str = "Завершено штатно (достигнут конец диапазона)"

    except KeyboardInterrupt:
        log_event(f"!!! ПРОЦЕСС ПРЕРВАН ПОЛЬЗОВАТЕЛЕМ (Ctrl+C) во время обработки аккаунта номер {current_account_number} !!!", important=True)
        script_should_terminate = True
        termination_reason_str = "Прервано пользователем (Ctrl+C)"
        last_account_for_termination = current_account_number
        if current_account_number not in [acc[0] for acc in failed_accounts_details]: 
             failed_accounts_details.append((current_account_number, "Прервано пользователем Ctrl+C"))
    except SystemExit as e: 
        log_event(f"Критическая ошибка на старте (SystemExit): {e}", important=True)
        # termination_reason_str и script_should_terminate уже установлены перед raise
    except Exception:
        script_should_terminate = True
        termination_reason_str = "Непредвиденное исключение в основном процессе."
        last_account_for_termination = current_account_number or None
        unhandled_exception_text = traceback.format_exc()
        log_event(f"КРИТИЧЕСКОЕ НЕПРЕДВИДЕННОЕ ИСКЛЮЧЕНИЕ:\n{unhandled_exception_text}", important=True)
    finally:
        log_event("============================== ЗАВЕРШЕНИЕ СЕАНСА ОБРАБОТКИ ==============================", important=True)
        final_exit_code = determine_exit_code()
        
        final_last_account_num_display = None # Для вывода в консоль
        if script_should_terminate and last_account_for_termination is not None:
             final_last_account_num_display = last_account_for_termination
        
        save_logs_summary() # Записывает только итоговую сводку в конец файла

        if final_exit_code not in (0, 130):
            try:
                write_failure_context(
                    reason=termination_reason_str,
                    account_number=last_account_for_termination or current_account_number or None,
                    exception_text=unhandled_exception_text,
                    exit_code=final_exit_code,
                )
            except Exception as context_error:
                print(f"!!! НЕ УДАЛОСЬ СОХРАНИТЬ КОНТЕКСТ СБОЯ: {type(context_error).__name__}: {context_error} !!!")

        if script_should_terminate:
            print(f"Работа скрипта была остановлена. Причина: {termination_reason_str}")
            if final_last_account_num_display is not None:
                print(f"Последний обрабатываемый номер аккаунта: {final_last_account_num_display}")
        else:
            print(f"Работа скрипта завершена: {termination_reason_str}")
        print(f"Все логи сессии сохранены в: {LOG_FILE_PATH}")
        if last_failure_context_path:
            print(f"Контекст сбоя для Codex CLI: {last_failure_context_path}")
        sys.exit(final_exit_code)
