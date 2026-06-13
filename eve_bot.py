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
import signal

from eve_config import describe_launcher_command, get_launcher_command, resource_path
from mail import find_latest_eve_verification_code, get_gmail_service

# --- Пользовательские настройки ---
SKILLS_FILE_PATH = "skills.txt"
OMEGA_SKILLS_FILE_PATH = os.environ.get("EVE_OMEGA_SKILLS_FILE", "skills2.txt")
LOG_FILE_PATH = "script_run_log.txt" # Логи будут писаться сюда непрерывно
FAILED_ACCOUNTS_LOG_FILE_PATH = os.environ.get("EVE_FAILED_ACCOUNTS_LOG_FILE", "failed_accounts.log")
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
START_ACTION_DELAY_SECONDS = float(os.environ.get("EVE_START_ACTION_DELAY_SECONDS", "0"))
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
POST_POPUP_CLOSE_SCAN_SECONDS = float(os.environ.get("EVE_POST_POPUP_CLOSE_SCAN_SECONDS", "0.5"))
TIMEOUT_GAME_REQUIRED_ACTION = int(os.environ.get("EVE_TIMEOUT_GAME_REQUIRED_ACTION", "15"))
TIMEOUT_GAME_REQUIRED_STATE = int(os.environ.get("EVE_TIMEOUT_GAME_REQUIRED_STATE", "20"))
TIMEOUT_GAME_OPTIONAL_ACTION = int(os.environ.get("EVE_TIMEOUT_GAME_OPTIONAL_ACTION", "4"))
TIMEOUT_GAME_STORE_LOAD = int(os.environ.get("EVE_TIMEOUT_GAME_STORE_LOAD", "60"))
TIMEOUT_GAME_GIFT_CLAIM = int(os.environ.get("EVE_TIMEOUT_GAME_GIFT_CLAIM", "90"))
TIMEOUT_GAME_CHARACTER_PICK = int(os.environ.get("EVE_TIMEOUT_GAME_CHARACTER_PICK", "60"))
TIMEOUT_GAME_SKILL_QUEUE_SUCCESS = int(os.environ.get("EVE_TIMEOUT_GAME_SKILL_QUEUE_SUCCESS", "30"))
TIMEOUT_GAME_UI_AFTER_3D_TOGGLE = int(os.environ.get("EVE_TIMEOUT_GAME_UI_AFTER_3D_TOGGLE", "8"))
TIMEOUT_GAME_QUIT_MENU_READY = int(os.environ.get("EVE_TIMEOUT_GAME_QUIT_MENU_READY", "25"))
TIMEOUT_GAME_EXIT_TO_LAUNCHER = int(os.environ.get("EVE_TIMEOUT_GAME_EXIT_TO_LAUNCHER", "120"))
TIMEOUT_LAUNCHER_RECOVERY = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_RECOVERY", "90"))
TIMEOUT_LAUNCHER_FOCUS_VERIFY = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_FOCUS_VERIFY", "4"))
TIMEOUT_LAUNCHER_ACCOUNT_REMOVAL_READY = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_ACCOUNT_REMOVAL_READY", "3"))
TIMEOUT_OPTIONAL_CONFIRM_DIALOG = int(os.environ.get("EVE_TIMEOUT_OPTIONAL_CONFIRM_DIALOG", "4"))
MAX_GAME_POPUP_CLOSE_ATTEMPTS = int(os.environ.get("EVE_MAX_GAME_POPUP_CLOSE_ATTEMPTS", "4"))
MAX_GAME_QUIT_MENU_ATTEMPTS = int(os.environ.get("EVE_MAX_GAME_QUIT_MENU_ATTEMPTS", "4"))
MAX_GAME_CONTRACT_VIEW_ATTEMPTS = int(os.environ.get("EVE_MAX_GAME_CONTRACT_VIEW_ATTEMPTS", "3"))
MAX_GAME_LEFT_MENU_OPEN_ATTEMPTS = int(os.environ.get("EVE_MAX_GAME_LEFT_MENU_OPEN_ATTEMPTS", "4"))
GAME_READY_STABLE_SECONDS = float(os.environ.get("EVE_GAME_READY_STABLE_SECONDS", "3"))
PAUSE_AFTER_DISABLE_3D_RENDERING = float(os.environ.get("EVE_PAUSE_AFTER_DISABLE_3D_RENDERING", "1.5"))
DISABLE_3D_RENDERING_ON_GAME_START = os.environ.get("EVE_DISABLE_3D_RENDERING_ON_GAME_START", "0").lower() not in {"0", "false", "no"}
DISABLE_3D_RENDERING_ATTEMPTS = int(os.environ.get("EVE_DISABLE_3D_RENDERING_ATTEMPTS", "2"))
DISABLE_3D_RENDERING_MIN_MEAN_DIFF = float(os.environ.get("EVE_DISABLE_3D_RENDERING_MIN_MEAN_DIFF", "4.0"))
REQUIRE_3D_RENDERING_TOGGLE_CONFIRMATION = os.environ.get("EVE_REQUIRE_3D_RENDERING_TOGGLE_CONFIRMATION", "1").lower() not in {"0", "false", "no"}
DISABLE_WINDOW_BLUR_ON_GAME_START = os.environ.get("EVE_DISABLE_WINDOW_BLUR_ON_GAME_START", "1").lower() not in {"0", "false", "no"}
DISABLE_WINDOW_BLUR_REQUIRED = os.environ.get("EVE_DISABLE_WINDOW_BLUR_REQUIRED", "0").lower() not in {"0", "false", "no"}
LAUNCHER_ALT_TAB_RECOVERY_ATTEMPTS = int(os.environ.get("EVE_LAUNCHER_ALT_TAB_RECOVERY_ATTEMPTS", "2"))
PAUSE_AFTER_LAUNCHER_ALT_TAB = float(os.environ.get("EVE_PAUSE_AFTER_LAUNCHER_ALT_TAB", "1.0"))
LAUNCHER_FULLSCREEN_ON_START = os.environ.get("EVE_LAUNCHER_FULLSCREEN_ON_START", "1").lower() not in {"0", "false", "no"}
LAUNCHER_READY_STABLE_SECONDS = float(os.environ.get("EVE_LAUNCHER_READY_STABLE_SECONDS", "3"))
LAUNCHER_FULLSCREEN_MIN_MEAN_DIFF = float(os.environ.get("EVE_LAUNCHER_FULLSCREEN_MIN_MEAN_DIFF", "4.0"))
LAUNCHER_FULLSCREEN_MIN_WIDTH_RATIO = float(os.environ.get("EVE_LAUNCHER_FULLSCREEN_MIN_WIDTH_RATIO", "0.85"))
LAUNCHER_FULLSCREEN_MIN_HEIGHT_RATIO = float(os.environ.get("EVE_LAUNCHER_FULLSCREEN_MIN_HEIGHT_RATIO", "0.85"))
TIMEOUT_LAUNCHER_AFTER_F11 = int(os.environ.get("EVE_TIMEOUT_LAUNCHER_AFTER_F11", "20"))
LAUNCHER_ACTION_RETRIES = int(os.environ.get("EVE_LAUNCHER_ACTION_RETRIES", "3"))
LAUNCHER_START_COMMAND_ATTEMPTS = int(os.environ.get("EVE_LAUNCHER_START_COMMAND_ATTEMPTS", "2"))
LAUNCHER_FOCUS_ATTEMPTS = int(os.environ.get("EVE_LAUNCHER_FOCUS_ATTEMPTS", "3"))
GAME_MY_CONTRACTS_CONFIDENCE = float(os.environ.get("EVE_GAME_MY_CONTRACTS_CONFIDENCE", "0.68"))
CONTRACT_SEARCH_BY_DROPDOWN_X_OFFSET = int(os.environ.get("EVE_CONTRACT_SEARCH_BY_DROPDOWN_X_OFFSET", "75"))
CONTRACT_ONLY_EXACT_PHRASE_DROPDOWN_Y_OFFSET = int(os.environ.get("EVE_CONTRACT_ONLY_EXACT_PHRASE_DROPDOWN_Y_OFFSET", "130"))
CONTRACT_SEARCH_DROPDOWN_PAUSE_SECONDS = float(os.environ.get("EVE_CONTRACT_SEARCH_DROPDOWN_PAUSE_SECONDS", "1.0"))
FAIL_SOFT_ACCOUNTS = os.environ.get("EVE_FAIL_SOFT_ACCOUNTS", "1").lower() not in {"0", "false", "no"}
ACCOUNT_FAILURE_DIAGNOSTICS = os.environ.get("EVE_ACCOUNT_FAILURE_DIAGNOSTICS", "1").lower() not in {"0", "false", "no"}
MAX_CONSECUTIVE_ACCOUNT_FAILURES = int(os.environ.get("EVE_MAX_CONSECUTIVE_ACCOUNT_FAILURES", "5"))
LAUNCHER_WINDOW_TITLE_PATTERNS = env_list("EVE_LAUNCHER_WINDOW_TITLE_PATTERNS", "eve launcher,eve online")
LAUNCHER_WINDOW_APP_ID_PATTERNS = env_list("EVE_LAUNCHER_WINDOW_APP_ID_PATTERNS", "evelauncher,eve,steam")
LAUNCHER_WINDOW_IGNORE_PATTERNS = env_list("EVE_LAUNCHER_WINDOW_IGNORE_PATTERNS", "tray")
EVE_TRAY_WINDOW_TITLE_PATTERNS = env_list("EVE_TRAY_WINDOW_TITLE_PATTERNS", "tray")
EVE_TRAY_WINDOW_APP_ID_PATTERNS = env_list("EVE_TRAY_WINDOW_APP_ID_PATTERNS", "steam_app_8500,evelauncher,eve,steam")
EVE_TRAY_WINDOW_MAX_WIDTH = int(os.environ.get("EVE_TRAY_WINDOW_MAX_WIDTH", "420"))
EVE_TRAY_WINDOW_MAX_HEIGHT = int(os.environ.get("EVE_TRAY_WINDOW_MAX_HEIGHT", "420"))
FORCE_CLEANUP_PROCESS_PATTERNS = env_list(
    "EVE_FORCE_CLEANUP_PROCESS_PATTERNS",
    "exefile.exe,evelauncher,eve-online.exe,eve online launcher,steam_app_8500",
)
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
GAME_NEW_EVENT_IMG = 'screens/game_new_event.png'
GAME_NEW_EVENT_CLOSE_BUTTON_IMG = 'screens/game_new_event_close_button.png'
GAME_OMEGA_STORE_ENTRY_IMG = 'screens/game_7_days_omega_offer_in_store_1.png'
GAME_OMEGA_OFFER_IMG = 'screens/game_7_days_omega_offer_in_store_2.png'
GAME_OMEGA_FREE_BUTTON_IMG = 'screens/game_7_days_omega_offer_in_store_3(free button).png'
GAME_LOG_OFF_BUTTON_IMG = 'screens/game_log_off_button.png'
GAME_LOG_OFF_YES_BUTTON_IMG = 'screens/game_log_off_yes_button.png'
GAME_GIFT_CLAIM_BUTTON_IMG = 'screens/game_gift_claim_button.png'
GAME_CHARACTER_PICK_IMG = 'screens/game_character_pick.png'
GAME_GIFTS_BUTTON_IMG = 'screens/game_gifts_button.png'
GAME_GIFTS_BUTTON_ALT_IMG = 'screens/game_gifts_button_alt.png'
GAME_GIFTS_SELECT_ALL_BUTTON_IMG = 'screens/game_gifts_select_all_button.png'
GAME_REDEEM_TO_CURRENT_STATION_IMG = 'screens/game_redeem_to_current_station.png'
GAME_REDEEM_YES_BUTTON_IMG = 'screens/game_redeem_yes_button.png'
GAME_EXPERT_SYSTEM_EVENT_IMG = 'screens/game_expert_system_event.png'
GAME_CLOSE_X2_IMG = 'screens/x2.png'
GAME_SKILLS_IMG = 'screens/game_skills.png'
GAME_SKILLS_ALT_IMG = 'screens/game_skills2.png'
GAME_SKILLS_MENU_IMG = 'screens/game_skills_menu.png'
GAME_SKILL_QUEUE_REPLACE_BUTTON_IMG = 'screens/game_skill_queue_replace_button.png'
GAME_SUCCESS_SKILL_IMG = 'screens/game_success_skill.png'
GAME_PLUS_BUTTON_IMG = 'screens/game_plus_button.png'
GAME_CONFIRM_BUTTON_IMG = 'screens/game_confirm_button.png'
GAME_CLOSE1_IMG = 'screens/game_close1.png'
GAME_CLOSE2_IMG = 'screens/game_close2.png'
GAME_CLOSE3_IMG = 'screens/game_close3.png'
GAME_QUIT_GAME_BUTTON_IMG = 'screens/game_quit_game_button.png'
GAME_YES_BUTTON_AFTER_QUIT_IMG = 'screens/game_yes_button_after_quit.png'
GAME_REWARD_POPUP_TITLE_IMG = 'screens/game_reward_popup_title.png'
GAME_UNDOCK_BUTTON_IMG = 'screens/game_undock_button.png'
GAME_UI_SETTING_IMG = 'screens/game_ui_setting.png'
GAME_ENABLE_WINDOW_BLUR_IMG = 'screens/game_enable_window_blur.png'
GAME_MENU_BUTTON_IMG = 'screens/game_menu_button.png'
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
GAME_LEAVE_CURRENT_SHIP_BUTTON_IMG = 'screens/game_leave_current_ship_button.png'
GAME_NOT_ENOUGH_SKILL_POINTS_ALERT_IMG = 'screens/game_not_enough_skill_points_alert.png'
GAME_SKILLS_ENGINEERING_IMG = 'screens/game_skills_engineering.png'
GAME_SKILL_ELECTRONIC_UPGRADES_IMG = 'screens/game_skill_electronic_upgrades.png'
GAME_SKILL_WEAPON_UPGRADES_IMG = 'screens/game_skill_weapon_upgrades.png'
GAME_SKILL_CPU_MANAGEMENT_IMG = 'screens/game_skill_cpu_management.png'
GAME_EXTRACT_SKILL_BUTTON_IMG = 'screens/game_extract_skill_button.png'
GAME_BIG_EXTRACT_BUTTON_IMG = 'screens/game_big_extract_button.png'
GAME_CLAIM_BUTTON_IMG = 'screens/game_claim_button.png'
GAME_LARGE_SKILL_INJECTOR_IMG = 'screens/game_large_skill_injector.png'
GAME_CREATE_CONTRACT_IMG = 'screens/game_create_contract.png'
GAME_PRIVATE_IMG = 'screens/game_private.png'
GAME_NAME_FIELD_IMG = 'screens/game_name.png'
GAME_SEARCH_BY_IMG = 'screens/game_search_by.png'
GAME_EXACT_PHRASE_MAIN_IMG = 'screens/game_exact_phrase_main.png'
GAME_EXACT_PHRASE_IMG = 'screens/game_exact_phrase.png'
GAME_ONLY_EXACT_PHRASE_IMG = 'screens/game_only_exact_phrase.png'
GAME_NEXT_BUTTON_IMG = 'screens/game_next_button.png'
GAME_TYPE_BOX_IMG = 'screens/game_type_box.png'
GAME_FINISH_BUTTON_IMG = 'screens/game_finish_button.png'
GAME_YES_BUTTON_IMG = 'screens/game_yes_button.png'
GAME_SUCCESS_SCREEN_IMG = 'screens/success_screen.png'
IMAGE_ONLY_UI = os.environ.get("EVE_IMAGE_ONLY_UI", "1").lower() not in {"0", "false", "no"}
IMAGE_MATCH_DIAGNOSTICS = os.environ.get("EVE_IMAGE_MATCH_DIAGNOSTICS", "0").lower() not in {"0", "false", "no"}
GAME_PROCESS_PATTERNS = [
    pattern.strip().lower()
    for pattern in os.environ.get("EVE_GAME_PROCESS_PATTERNS", "exefile.exe").split(",")
    if pattern.strip()
]

EVE_ACCOUNT_USERNAME_PREFIX = os.environ.get("EVE_ACCOUNT_USERNAME_PREFIX", "my.eve.online.")
EVE_ACCOUNT_PASSWORD = os.environ.get("EVE_ACCOUNT_PASSWORD")
END_ACCOUNT_RANGE_FIXED = None
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
clipboard_owner_processes = []
window_blur_disable_completed = False


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


def save_current_screenshot_evidence(label):
    try:
        image = pyautogui.screenshot().convert("RGB")
    except Exception as exc:
        log_event(f"Не удалось сохранить evidence screenshot '{label}': {type(exc).__name__}: {exc}", important=True)
        return None
    return save_runtime_evidence_image(image, label)


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


def read_account_range_from_env():
    start_raw = os.environ.get("EVE_START_ACCOUNT", "31").strip()
    last_raw = (
        os.environ.get("EVE_LAST_ACCOUNT")
        or os.environ.get("EVE_END_ACCOUNT")
        or "2000"
    ).strip()
    last_source = "EVE_LAST_ACCOUNT" if os.environ.get("EVE_LAST_ACCOUNT") else "EVE_END_ACCOUNT"

    try:
        start_account = int(start_raw)
        last_account = int(last_raw)
    except ValueError as exc:
        raise ValueError(
            "EVE_START_ACCOUNT и EVE_LAST_ACCOUNT должны быть целыми числами "
            f"(получено start='{start_raw}', last='{last_raw}')."
        ) from exc

    if start_account < 1:
        raise ValueError(f"EVE_START_ACCOUNT должен быть >= 1, получено {start_account}.")
    if last_account < 1:
        raise ValueError(f"{last_source} должен быть >= 1, получено {last_account}.")
    if start_account > last_account:
        raise ValueError(
            "EVE_START_ACCOUNT не может быть больше последнего аккаунта: "
            f"{start_account} > {last_account}."
        )

    log_event(
        f"Диапазон аккаунтов взят из env: EVE_START_ACCOUNT={start_account}, "
        f"{last_source}={last_account} включительно."
    )
    return start_account, last_account


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


def launcher_fullscreen_confirmation_templates():
    return [
        (LAUNCHER_FULLSCREEN_IMG, "Launcher fullscreen layout"),
        (LAUNCHER_FULLSCREEN_READY_STATUS_IMG, "Fullscreen launcher ready status"),
        (LAUNCHER_FULLSCREEN_ACCOUNT_HEADER_IMG, "Fullscreen Account Settings header"),
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
    ]


def game_visible_templates():
    return [
        *game_ready_templates(),
        (GAME_GIFTS_BUTTON_IMG, "Gifts button"),
        (GAME_SKILLS_IMG, "Skills"),
        (GAME_SKILLS_ALT_IMG, "Skills alternate"),
        (GAME_MENU_BUTTON_IMG, "Game left menu button"),
        (GAME_INVENTORY_ICON_IMG, "Inventory icon"),
    ]


def game_esc_menu_templates():
    return [
        (GAME_UI_SETTING_IMG, "User Interface settings"),
        (GAME_QUIT_GAME_BUTTON_IMG, "Quit Game"),
    ]


def game_ui_after_3d_toggle_templates():
    return [
        *game_ready_templates(),
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


def skill_extraction_progress_templates():
    return [
    (GAME_SKILLS_ENGINEERING_IMG, "Skills Engineering"),
    (GAME_SKILL_ELECTRONIC_UPGRADES_IMG, "Electronic Upgrades skill"),
    (GAME_SKILL_WEAPON_UPGRADES_IMG, "Weapon Upgrades skill"),
    (GAME_SKILL_CPU_MANAGEMENT_IMG, "CPU Management skill"),
        (GAME_EXTRACT_SKILL_BUTTON_IMG, "Extract Skill button"),
        (GAME_BIG_EXTRACT_BUTTON_IMG, "Big Extract button"),
    ]


def omega_store_templates():
    return [
        (GAME_OMEGA_STORE_ENTRY_IMG, "7 days Omega offer store entry"),
        (GAME_OMEGA_OFFER_IMG, "7 days Omega offer details"),
        (GAME_OMEGA_FREE_BUTTON_IMG, "7 days Omega free button"),
    ]


def gift_redeem_templates():
    return [
        (GAME_GIFT_CLAIM_BUTTON_IMG, "Gift claim button"),
        (GAME_CHARACTER_PICK_IMG, "Character pick"),
        (GAME_GIFTS_BUTTON_IMG, "Gifts button"),
        (GAME_REDEEM_TO_CURRENT_STATION_IMG, "Redeem to current station"),
        (GAME_REDEEM_YES_BUTTON_IMG, "Redeem yes"),
        (GAME_EXPERT_SYSTEM_EVENT_IMG, "Expert system event"),
    ]


def skill_queue_templates():
    return [
        (GAME_SKILLS_IMG, "Skills"),
        (GAME_SKILLS_ALT_IMG, "Skills alternate"),
        (GAME_SKILLS_MENU_IMG, "Skills menu"),
        (GAME_SKILL_QUEUE_REPLACE_BUTTON_IMG, "Replace skill queue"),
        (GAME_SUCCESS_SKILL_IMG, "Skill queue import success"),
        (GAME_PLUS_BUTTON_IMG, "Plus button"),
        (GAME_CONFIRM_BUTTON_IMG, "Confirm button"),
        (GAME_CLOSE1_IMG, "Close button 1"),
        (GAME_CLOSE2_IMG, "Close button 2"),
        (GAME_CLOSE3_IMG, "Close button 3"),
    ]


def final_large_skill_injector_contract_templates():
    return [
        (GAME_CLAIM_BUTTON_IMG, "ISK claim button"),
        (GAME_LARGE_SKILL_INJECTOR_IMG, "Large Skill Injector"),
        (GAME_CREATE_CONTRACT_IMG, "Create Contract"),
        (GAME_PRIVATE_IMG, "Private contract"),
        (GAME_NAME_FIELD_IMG, "Contract name field"),
        (GAME_SEARCH_BY_IMG, "Search By label"),
        (GAME_EXACT_PHRASE_MAIN_IMG, "Exact phrase main"),
        (GAME_EXACT_PHRASE_IMG, "Exact phrase"),
        (GAME_ONLY_EXACT_PHRASE_IMG, "Only exact phrase"),
        (GAME_NEXT_BUTTON_IMG, "Next button"),
        (GAME_TYPE_BOX_IMG, "Type checkbox"),
        (GAME_FINISH_BUTTON_IMG, "Finish button"),
        (GAME_YES_BUTTON_IMG, "Yes button"),
        (GAME_SUCCESS_SCREEN_IMG, "Success screen"),
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

    if launcher_fullscreen_size_confirmed("лаунчер перед F11"):
        log_event("F11 не требуется: лаунчер уже fullscreen по размеру окна.", important=True)
        return True

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
            log_event("F11 не дал достаточного визуального изменения; проверяем реальный размер окна.", important=True)

    if not wait_for_stable_launcher_ready(
        "лаунчер после F11",
        timeout_seconds=TIMEOUT_LAUNCHER_AFTER_F11,
    )[0]:
        log_event("ОШИБКА: после F11 лаунчер не стабилизировался. Продолжать небезопасно.", important=True)
        return False

    if launcher_fullscreen_size_confirmed("лаунчер после F11"):
        log_event("F11 подтверждён: лаунчер fullscreen по размеру niri.", important=True)
        return True

    log_event("F11 не сделал лаунчер fullscreen по размеру niri. Пробуем niri fullscreen fallback.", important=True)
    if not force_launcher_fullscreen_with_niri("launcher fullscreen fallback"):
        log_event("ОШИБКА: лаунчер не удалось перевести в fullscreen через F11 или niri fallback.", important=True)
        return False

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


def get_niri_window_size(window):
    layout = window.get("layout")
    if not isinstance(layout, dict):
        return None, None

    for key in ("window_size", "tile_size"):
        value = layout.get(key)
        if isinstance(value, list) and len(value) >= 2:
            try:
                return int(value[0]), int(value[1])
            except (TypeError, ValueError):
                continue
    return None, None


def get_screen_size_for_window_checks():
    try:
        size = pyautogui.size()
        return int(size.width), int(size.height)
    except Exception as exc:
        log_event(f"Не удалось получить размер экрана для проверки fullscreen: {type(exc).__name__}: {exc}")
        return None, None


def is_niri_window_fullscreen_sized(window):
    width, height = get_niri_window_size(window)
    screen_width, screen_height = get_screen_size_for_window_checks()
    if not width or not height or not screen_width or not screen_height:
        return False

    return (
        width >= int(screen_width * LAUNCHER_FULLSCREEN_MIN_WIDTH_RATIO)
        and height >= int(screen_height * LAUNCHER_FULLSCREEN_MIN_HEIGHT_RATIO)
    )


def get_best_launcher_window_for_fullscreen_check():
    candidates = get_launcher_window_candidates()
    if not candidates:
        return None
    return candidates[0][1]


def log_launcher_fullscreen_size(window, context_description):
    width, height = get_niri_window_size(window)
    screen_width, screen_height = get_screen_size_for_window_checks()
    log_event(
        f"{context_description}: launcher window size={width}x{height}, "
        f"screen={screen_width}x{screen_height}, "
        f"required>={LAUNCHER_FULLSCREEN_MIN_WIDTH_RATIO:.2f}w/"
        f"{LAUNCHER_FULLSCREEN_MIN_HEIGHT_RATIO:.2f}h."
    )


def launcher_fullscreen_size_confirmed(context_description):
    window = get_best_launcher_window_for_fullscreen_check()
    if not window:
        log_event(f"{context_description}: окно лаунчера не найдено для проверки fullscreen.", important=True)
        return False

    log_launcher_fullscreen_size(window, context_description)
    if is_niri_window_fullscreen_sized(window):
        log_event(f"{context_description}: fullscreen подтверждён размером окна niri.", important=True)
        return True
    return False


def toggle_niri_window_fullscreen(window, action_name, context_description):
    window_id = window.get("id")
    if window_id is None:
        return False

    log_event(f"{context_description}: выполняем niri {action_name} для {niri_window_summary(window)}.", important=True)
    try:
        result = subprocess.run(
            ["niri", "msg", "action", action_name, "--id", str(window_id)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        log_event(f"{context_description}: niri {action_name} не выполнен: {type(exc).__name__}: {exc}", important=True)
        return False

    if result.returncode != 0:
        error_text = result.stderr.strip()
        log_event(f"{context_description}: niri {action_name} вернул ошибку: {error_text or result.returncode}", important=True)
        return False
    time.sleep(PAUSE_AFTER_F11_ATTEMPT)
    return True


def force_launcher_fullscreen_with_niri(context_description):
    window = get_best_launcher_window_for_fullscreen_check()
    if not window:
        log_event(f"{context_description}: лаунчер не найден для niri fullscreen fallback.", important=True)
        return False

    if is_niri_window_fullscreen_sized(window):
        log_event(f"{context_description}: лаунчер уже fullscreen по размеру, niri fallback не нужен.", important=True)
        return True

    if not toggle_niri_window_fullscreen(window, "fullscreen-window", context_description):
        return False

    if launcher_fullscreen_size_confirmed(f"{context_description}: после niri fullscreen-window"):
        return True

    window = get_best_launcher_window_for_fullscreen_check()
    if not window:
        return False
    if not toggle_niri_window_fullscreen(window, "toggle-windowed-fullscreen", context_description):
        return False

    return launcher_fullscreen_size_confirmed(f"{context_description}: после niri windowed fullscreen")


def is_eve_tray_helper_window(window):
    title = get_window_text(window, "title").lower()
    app_id = get_window_text(window, "app_id", "app-id").lower()
    combined = f"{title} {app_id}"

    if any(pattern in combined for pattern in EVE_TRAY_WINDOW_TITLE_PATTERNS):
        return True

    width, height = get_niri_window_size(window)
    if width is None or height is None:
        return False

    is_small = width <= EVE_TRAY_WINDOW_MAX_WIDTH and height <= EVE_TRAY_WINDOW_MAX_HEIGHT
    is_eve_related = any(pattern in combined for pattern in EVE_TRAY_WINDOW_APP_ID_PATTERNS)
    if is_small and is_eve_related:
        return True

    return False


def rank_launcher_window(window):
    title = get_window_text(window, "title").lower()
    app_id = get_window_text(window, "app_id", "app-id").lower()
    combined = f"{title} {app_id}"

    if any(pattern in combined for pattern in LAUNCHER_WINDOW_IGNORE_PATTERNS):
        return 0
    if is_eve_tray_helper_window(window):
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
    if is_eve_tray_helper_window(window):
        return 0

    score = 0
    if title.startswith("eve -"):
        score = max(score, 100)
    elif title.startswith("eve"):
        score = max(score, 80)

    if "steam_app_8500" in app_id:
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


def wait_for_niri_window_focus(window_id, context_description, timeout_seconds=2.0):
    if window_id is None:
        return False

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        for window in get_niri_windows():
            if window.get("id") == window_id and window.get("is_focused"):
                log_event(f"{context_description}: niri подтвердил фокус окна id={window_id}.")
                return True
        time.sleep(PAUSE_SHORT)

    log_event(f"{context_description}: niri не подтвердил фокус окна id={window_id}.", important=True)
    return False


def launcher_focus_confirmed_by_niri(context_description):
    candidates = get_launcher_window_candidates()
    for score, window in candidates:
        if window.get("is_focused"):
            log_event(
                f"{context_description}: niri подтверждает сфокусированный лаунчер: "
                f"{niri_window_summary(window)} score={score}."
            )
            return True
    log_event(f"{context_description}: niri не подтверждает фокус лаунчера.", important=True)
    return False


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
            game_visible_templates(),
            "игра после niri focus",
            timeout_seconds=verify_timeout_seconds,
            confidence_level=0.75,
        )[0]:
            log_event("Окно игры подтверждено после niri focus.", important=True)
            return True
        log_event("Окно игры сфокусировано, но игровая UI-проверка не подтвердилась.", important=True)

    return False


def focus_game_for_ui_action(context_description):
    if focus_existing_game_window(context_description):
        return True

    log_event(
        f"{context_description}: niri не подтвердил окно игры. Пробуем сфокусировать видимый игровой UI кликом по image anchor.",
        important=True,
    )
    focus_anchors = game_visible_templates()
    image_filename, image_description, location = wait_for_optional_image(
        focus_anchors,
        f"{context_description}: видимый игровой UI для fallback focus",
        timeout_seconds=TIMEOUT_LAUNCHER_FOCUS_VERIFY,
        confidence_level=0.75,
    )
    if not location:
        log_event(f"{context_description}: fallback focus невозможен, игровой UI не найден.", important=True)
        return False

    click_screen_location_custom(location, f"{image_description} для фокуса игры")
    time.sleep(PAUSE_MEDIUM)
    if wait_for_optional_image(
        game_visible_templates(),
        f"{context_description}: игра после fallback focus",
        timeout_seconds=TIMEOUT_LAUNCHER_FOCUS_VERIFY,
        confidence_level=0.75,
    )[0]:
        log_event(f"{context_description}: игра подтверждена после fallback focus.", important=True)
        return True

    log_event(f"{context_description}: fallback focus клик был выполнен, но игровой UI не подтвердился.", important=True)
    return False


def ensure_game_esc_menu_open(context_description, attempts=3):
    image_filename, image_description, _ = wait_for_optional_image(
        game_esc_menu_templates(),
        f"{context_description}: уже открытое Esc-меню",
        timeout_seconds=1,
        confidence_level=0.75,
    )
    if image_filename:
        log_event(f"{context_description}: Esc-меню уже открыто: '{image_description}' ({image_filename}).")
        return True

    for attempt in range(1, attempts + 1):
        if not focus_game_for_ui_action(f"{context_description}: фокус перед Esc attempt {attempt}"):
            continue

        log_event(f"{context_description}: открываем Esc-меню, попытка {attempt}/{attempts}.")
        pyautogui.press("esc")
        time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)

        image_filename, image_description, _ = wait_for_optional_image(
            game_esc_menu_templates(),
            f"{context_description}: Esc-меню после Esc",
            timeout_seconds=TIMEOUT_GAME_QUIT_MENU_READY,
            confidence_level=0.75,
        )
        if image_filename:
            log_event(f"{context_description}: Esc-меню подтверждено: '{image_description}' ({image_filename}).")
            return True

        log_event(f"{context_description}: Esc-меню не подтвердилось после попытки {attempt}.", important=True)

    log_event(f"{context_description}: Esc-меню не удалось открыть и подтвердить.", important=True)
    return False


def wait_for_launcher_visible_optional(description, timeout_seconds=1):
    return wait_for_optional_image(
        launcher_visibility_templates(),
        description,
        timeout_seconds=timeout_seconds,
        confidence_level=0.75,
    )[0] is not None


def press_alt_tab_for_launcher_recovery():
    pyautogui.keyDown("alt")
    time.sleep(PAUSE_SHORT)
    pyautogui.press("tab")
    time.sleep(PAUSE_SHORT)
    pyautogui.keyUp("alt")


def recover_launcher_with_alt_tab(context_description, require_focus=False):
    if LAUNCHER_ALT_TAB_RECOVERY_ATTEMPTS <= 0:
        return False

    log_event(
        f"{context_description}: niri/image recovery не подтвердил лаунчер. "
        f"Пробуем Alt+Tab {LAUNCHER_ALT_TAB_RECOVERY_ATTEMPTS} раз.",
        important=True,
    )
    for attempt in range(1, LAUNCHER_ALT_TAB_RECOVERY_ATTEMPTS + 1):
        log_event(f"Alt+Tab recovery лаунчера, попытка {attempt}/{LAUNCHER_ALT_TAB_RECOVERY_ATTEMPTS}.")
        press_alt_tab_for_launcher_recovery()
        time.sleep(PAUSE_AFTER_LAUNCHER_ALT_TAB)
        if wait_for_launcher_visible_optional(
            "лаунчер после Alt+Tab recovery",
            timeout_seconds=TIMEOUT_LAUNCHER_FOCUS_VERIFY,
        ):
            if require_focus and not launcher_focus_confirmed_by_niri("лаунчер после Alt+Tab recovery"):
                continue
            log_event("Лаунчер подтверждён после Alt+Tab recovery.", important=True)
            return True
    return False


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
            focus_confirmed = wait_for_niri_window_focus(
                window_id,
                "лаунчер после niri focus",
                timeout_seconds=2.0,
            )
            launcher_visible = wait_for_launcher_visible_optional(
                "лаунчер после niri focus",
                timeout_seconds=TIMEOUT_LAUNCHER_FOCUS_VERIFY,
            )
            if launcher_visible and (focus_confirmed or not force_focus):
                log_event("Лаунчер подтверждён после фокусировки существующего окна niri.", important=True)
                return True
            if launcher_visible and not focus_confirmed:
                log_event(
                    "Лаунчер виден, но фокус niri не подтверждён. Продолжаем recovery, чтобы не слать клики в другое окно.",
                    important=True,
                )

        time.sleep(PAUSE_MEDIUM)

    if recover_launcher_with_alt_tab(context_description, require_focus=force_focus):
        return True

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


def disable_window_blur_after_game_start():
    global window_blur_disable_completed

    if not DISABLE_WINDOW_BLUR_ON_GAME_START:
        log_event("Отключение window blur пропущено: EVE_DISABLE_WINDOW_BLUR_ON_GAME_START=0.")
        return True

    if window_blur_disable_completed:
        log_event("Отключение window blur уже выполнялось в этом процессе; повторный toggle пропущен.")
        return True

    log_event("Отключаем прозрачность/blur UI через Esc -> User Interface -> Enable window blur.", important=True)
    if not focus_game_for_ui_action("Перед отключением window blur"):
        if DISABLE_WINDOW_BLUR_REQUIRED:
            return False
        log_event("Window blur не отключён: игру не удалось сфокусировать. Продолжаем, так как EVE_DISABLE_WINDOW_BLUR_REQUIRED=0.", important=True)
        return True

    if not ensure_game_esc_menu_open("Перед отключением window blur"):
        if DISABLE_WINDOW_BLUR_REQUIRED:
            return False
        log_event("Window blur не отключён: Esc-меню не открылось. Продолжаем, так как EVE_DISABLE_WINDOW_BLUR_REQUIRED=0.", important=True)
        return True

    if not click_image_until_state(
        GAME_UI_SETTING_IMG,
        "User Interface settings",
        [(GAME_ENABLE_WINDOW_BLUR_IMG, "Enable window blur setting")],
        "Enable window blur option",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=2,
    ):
        pyautogui.press("esc")
        time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)
        if DISABLE_WINDOW_BLUR_REQUIRED:
            return False
        log_event("Window blur не отключён: User Interface/Enable window blur не найдены. Продолжаем, так как EVE_DISABLE_WINDOW_BLUR_REQUIRED=0.", important=True)
        return True

    if not click_on_image(
        GAME_ENABLE_WINDOW_BLUR_IMG,
        "Enable window blur setting",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        pyautogui.press("esc")
        time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)
        if DISABLE_WINDOW_BLUR_REQUIRED:
            return False
        log_event("Window blur не отключён: click по Enable window blur не выполнен. Продолжаем, так как EVE_DISABLE_WINDOW_BLUR_REQUIRED=0.", important=True)
        return True

    time.sleep(PAUSE_MEDIUM)
    pyautogui.press("esc")
    time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)

    if not wait_for_optional_image(
        game_visible_templates(),
        "игровой UI после отключения window blur",
        timeout_seconds=TIMEOUT_GAME_REQUIRED_STATE,
        confidence_level=0.75,
    )[0]:
        if DISABLE_WINDOW_BLUR_REQUIRED:
            return False
        log_event("Window blur toggle выполнен, но игровой UI после Esc не подтверждён. Продолжаем, так как EVE_DISABLE_WINDOW_BLUR_REQUIRED=0.", important=True)
        return True

    window_blur_disable_completed = True
    log_event("Window blur toggle выполнен и игровой UI подтверждён.", important=True)
    return True


def reset_window_blur_disable_state_for_new_game(current_username):
    global window_blur_disable_completed
    if window_blur_disable_completed:
        log_event(
            f"Сбрасываем флаг window blur перед новым игровым клиентом для {current_username}; "
            "отключение blur будет выполнено заново.",
            important=True,
        )
    window_blur_disable_completed = False


def disable_3d_rendering_after_game_start():
    if not DISABLE_3D_RENDERING_ON_GAME_START:
        log_event(
            "Отключение 3D-рендеринга не выполняется: EVE_DISABLE_3D_RENDERING_ON_GAME_START=0. "
            "Продолжаем в обычном 3D-режиме."
        )
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

        ui_image, ui_description, _ = wait_for_optional_image(
            game_ui_after_3d_toggle_templates(),
            "игровой UI после Ctrl+Shift+F9",
            timeout_seconds=TIMEOUT_GAME_UI_AFTER_3D_TOGGLE,
            confidence_level=0.75,
        )
        if not ui_image:
            launcher_image, launcher_description, _ = find_first_available_image(
                launcher_after_game_exit_templates(),
                confidence_level=0.75,
                logged_errors=set(),
            )
            current_game_processes = get_game_process_ids()
            if launcher_image:
                log_event(
                    "ОШИБКА: после Ctrl+Shift+F9 виден лаунчер, а не игра: "
                    f"'{launcher_description}' ({launcher_image}).",
                    important=True,
                )
            if not current_game_processes:
                log_event("ОШИБКА: после Ctrl+Shift+F9 процесс игры не найден.", important=True)
            log_event(
                "ОШИБКА: Ctrl+Shift+F9 не подтверждён игровым UI. "
                "Внутриигровые клики и клавиши запрещены.",
                important=True,
            )
            return False

        log_event(f"Игровой UI после Ctrl+Shift+F9 подтверждён: '{ui_description}' ({ui_image}).")

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


def click_launcher_image_until_state(
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
        log_event(f"Попытка {attempt}/{attempts}: {description} с обязательным фокусом лаунчера.")
        if not recover_existing_launcher_visibility(f"лаунчер перед кликом '{description}'", force_focus=True):
            continue

        found_image, found_description, _ = wait_for_optional_image(
            success_templates,
            f"{success_description} перед повторным кликом '{description}'",
            timeout_seconds=1,
            confidence_level=confidence_level,
        )
        if found_image:
            log_event(
                f"Ожидаемое состояние для '{description}' уже открыто: "
                f"'{found_description}' ({found_image})."
            )
            return True

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

        log_event(f"Post-click проверка '{description}' не подтвердила состояние '{success_description}'. Повторяем с повторным фокусом лаунчера.", important=True)

    log_event(f"ОШИБКА: '{description}' не привело к состоянию '{success_description}' после {attempts} попыток.", important=True)
    return False


def existing_image_options(image_options):
    return [
        (image_filename, image_description)
        for image_filename, image_description in image_options
        if resource_path(image_filename).exists()
    ]


def click_first_image_until_state(
    image_options,
    description,
    success_templates,
    success_description,
    confidence_level=0.8,
    click_timeout_seconds=10,
    verify_timeout_seconds=5,
    attempts=LAUNCHER_ACTION_RETRIES,
):
    options = existing_image_options(image_options)
    if not options:
        log_event(f"ОШИБКА: нет существующих templates для '{description}'.", important=True)
        return False

    for attempt in range(1, attempts + 1):
        log_event(f"Попытка {attempt}/{attempts}: {description} (вариантов: {len(options)}).")
        _, image_description, location = wait_for_optional_image(
            options,
            description,
            timeout_seconds=click_timeout_seconds,
            confidence_level=confidence_level,
        )
        if not location:
            continue

        human_click(location.x, location.y)
        log_event(f"Клик по '{description}' выполнен через '{image_description}'.")
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


def click_launcher_image_until_disappears(
    image_filename,
    description,
    confidence_level=0.8,
    click_timeout_seconds=10,
    disappear_timeout_seconds=10,
    attempts=LAUNCHER_ACTION_RETRIES,
):
    clicked_at_least_once = False
    for attempt in range(1, attempts + 1):
        log_event(f"Попытка {attempt}/{attempts}: {description} с обязательным фокусом лаунчера.")
        if clicked_at_least_once and wait_for_image_to_disappear(
            image_filename,
            description,
            confidence_level=confidence_level,
            timeout_seconds=1,
        ):
            log_event(f"'{description}' уже исчезло после предыдущего клика. Считаем действие подтверждённым.")
            return True

        if not recover_existing_launcher_visibility(f"лаунчер перед кликом '{description}'", force_focus=True):
            continue

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

        log_event(f"Post-click проверка '{description}' не подтвердила исчезновение. Повторяем с повторным фокусом лаунчера.", important=True)

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
            if closed_count > 0:
                log_event("После закрытого popup новых popup не найдено; продолжаем без ожидания полного таймаута.")
                break
            time.sleep(PAUSE_SHORT)
            continue

        human_click(location.x, location.y)
        closed_count += 1
        log_event(f"Закрыто игровое окно '{image_description}' ({image_filename}).")
        time.sleep(PAUSE_SHORT)
        deadline = min(deadline, time.time() + POST_POPUP_CLOSE_SCAN_SECONDS)

    if closed_count >= MAX_GAME_POPUP_CLOSE_ATTEMPTS:
        log_event(f"Достигнут лимит закрытия popup за один аккаунт: {MAX_GAME_POPUP_CLOSE_ATTEMPTS}.", important=True)

    log_event(f"Проверка всплывающих игровых окон завершена. Закрыто: {closed_count}.")
    return True


def wait_for_game_finance_button(description, timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION):
    return wait_for_optional_image(
        [(GAME_FINANCE_BUTTON_IMG, "Finance button")],
        description,
        timeout_seconds=timeout_seconds,
        confidence_level=0.75,
    )


def click_finance_button_from_left_menu():
    image_filename, image_description, location = wait_for_game_finance_button(
        "кнопка Finance в левом меню",
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    )
    if not location:
        return False

    log_event(f"Finance найден: '{image_description}' ({image_filename}).")
    click_screen_location_custom(location, "кнопка Finance в левом меню")
    return True


def press_game_left_menu_key():
    pyautogui.keyDown('\\')
    time.sleep(0.05)
    pyautogui.keyUp('\\')


def open_game_left_menu():
    if wait_for_game_finance_button("левое меню уже открыто", timeout_seconds=1)[0]:
        return True

    for attempt in range(1, MAX_GAME_LEFT_MENU_OPEN_ATTEMPTS + 1):
        if not focus_game_for_ui_action("Перед открытием левого меню игры"):
            log_event("Фокус игры перед открытием левого меню не подтверждён. Повторяем.", important=True)
            continue

        if wait_for_game_finance_button("Finance после фокуса игры", timeout_seconds=1)[0]:
            log_event("Левое меню уже открыто после фокуса/fallback-клика: Finance виден.", important=True)
            return True

        log_event(
            f"Открываем левое меню игры через game_menu_button, "
            f"попытка {attempt}/{MAX_GAME_LEFT_MENU_OPEN_ATTEMPTS}."
        )
        if click_image_until_state(
            GAME_MENU_BUTTON_IMG,
            "Game menu button",
            [(GAME_FINANCE_BUTTON_IMG, "Finance button")],
            "Finance после game_menu_button",
            confidence_level=0.75,
            click_timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
            verify_timeout_seconds=3,
            attempts=1,
        ):
            log_event("Левое меню открыто через game_menu_button: Finance виден.", important=True)
            return True

        log_event("game_menu_button не открыл меню. Пробуем fallback через клавишу '\\'.", important=True)
        log_event(
            f"Открываем левое меню игры клавишей '\\', "
            f"попытка {attempt}/{MAX_GAME_LEFT_MENU_OPEN_ATTEMPTS}."
        )
        press_game_left_menu_key()
        time.sleep(PAUSE_MEDIUM)
        if wait_for_game_finance_button("Finance после клавиши '\\'", timeout_seconds=3)[0]:
            log_event("Левое меню открыто клавишей '\\': Finance виден.", important=True)
            return True

        log_event("Finance не найден после клавиши '\\'. Повторяем открытие меню без Neocom fallback.", important=True)

        log_event("Левое меню не подтвердилось. Следующая попытка.", important=True)

    log_event("ОШИБКА: левое меню игры не открылось по подтверждению Finance.", important=True)
    return False


def open_game_left_menu_and_click_finance():
    if not open_game_left_menu():
        return False
    return click_finance_button_from_left_menu()


def wait_for_my_contracts_button(description, timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION):
    return wait_for_optional_image(
        [(GAME_MY_CONTRACTS_BUTTON_IMG, "My Contracts")],
        description,
        timeout_seconds=timeout_seconds,
        confidence_level=GAME_MY_CONTRACTS_CONFIDENCE,
    )


def open_contracts_section():
    if wait_for_my_contracts_button("My Contracts уже виден", timeout_seconds=2)[0]:
        log_event("Contracts section уже открыт: My Contracts виден.")
        return True

    for attempt in range(1, 3):
        log_event(f"Открываем Contracts section, попытка {attempt}/2.")
        if not click_on_image(
            GAME_CONTRACTS_BUTTON_IMG,
            "Contracts",
            confidence_level=0.75,
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        ):
            continue

        close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_QUICK_SCAN)
        found_image, found_description, _ = wait_for_my_contracts_button(
            "My Contracts после клика Contracts",
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        )
        if found_image:
            log_event(f"Post-click проверка Contracts успешна: найдено '{found_description}' ({found_image}).")
            return True

        save_current_screenshot_evidence(f"my_contracts_not_visible_after_contracts_attempt_{attempt}")
        log_event("My Contracts не подтвердился после клика Contracts. Повторяем.", important=True)

    log_event("ОШИБКА: Contracts не привёл к видимому My Contracts.", important=True)
    return False


def click_my_contracts_button(attempt):
    close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_QUICK_SCAN)
    image_filename, image_description, location = wait_for_my_contracts_button(
        f"My Contracts перед кликом, попытка {attempt}",
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    )
    if not location:
        save_current_screenshot_evidence(f"my_contracts_not_found_attempt_{attempt}")
        log_event("My Contracts не найден перед кликом. Пробуем заново открыть Contracts section.", important=True)
        if not open_contracts_section():
            return False
        image_filename, image_description, location = wait_for_my_contracts_button(
            f"My Contracts после повторного открытия Contracts, попытка {attempt}",
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        )
        if not location:
            save_current_screenshot_evidence(f"my_contracts_still_not_found_attempt_{attempt}")
            return False

    log_event(f"My Contracts найден: '{image_description}' ({image_filename}).")
    return click_screen_location_custom(
        location,
        "My Contracts",
        button="left",
        clicks=1,
        interval=0.2,
    )


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

        if not click_my_contracts_button(attempt):
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
    save_current_screenshot_evidence("contract_name_not_found")
    return None


def read_required_text_file(filepath, description):
    try:
        with open(resource_path(filepath), "r", encoding="utf-8") as file_reader:
            text = file_reader.read()
    except FileNotFoundError:
        log_event(f"ОШИБКА: {description} не найден: {filepath}", important=True)
        return None
    except Exception as exc:
        log_event(f"ОШИБКА чтения {description} '{filepath}': {type(exc).__name__}: {exc}", important=True)
        return None

    if not text.strip():
        log_event(f"ОШИБКА: {description} пустой: {filepath}", important=True)
        return None
    return text


def set_text_for_proton_clipboard(text_value):
    clipboard_owner_attempts = []

    if shutil.which("xclip"):
        clipboard_owner_attempts.append(("xclip", ["xclip", "-selection", "clipboard", "-i"]))
    if shutil.which("xsel"):
        clipboard_owner_attempts.append(("xsel", ["xsel", "--clipboard", "--input"]))
    if shutil.which("wl-copy"):
        clipboard_owner_attempts.append(("wl-copy", ["wl-copy", "--foreground"]))

    for tool_name, command in clipboard_owner_attempts:
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            process.stdin.write(text_value)
            process.stdin.close()
            time.sleep(0.3)
        except Exception as exc:
            log_event(f"{tool_name}: не удалось записать clipboard: {type(exc).__name__}: {exc}", important=True)
            continue

        return_code = process.poll()
        if return_code is None:
            clipboard_owner_processes.append(process)
            log_event(f"Текст skill queue записан в clipboard через {tool_name}; clipboard owner оставлен активным.")
            return True

        if return_code == 0:
            log_event(f"Текст skill queue записан в clipboard через {tool_name}; процесс завершился штатно.")
            return True

        error_text = process.stderr.read().strip() if process.stderr else ""
        log_event(f"{tool_name}: clipboard owner вернул код {return_code}: {error_text}", important=True)

    try:
        pyperclip.copy(text_value)
        log_event("Текст skill queue записан через pyperclip fallback.")
        return True
    except Exception as exc:
        log_event(f"pyperclip fallback не смог записать clipboard: {type(exc).__name__}: {exc}", important=True)
        return False


def skill_queue_state_templates():
    return [
        (GAME_SUCCESS_SKILL_IMG, "Skill queue import success"),
        (GAME_SKILL_QUEUE_REPLACE_BUTTON_IMG, "Replace skill queue"),
        (GAME_CONFIRM_BUTTON_IMG, "Confirm button"),
        (GAME_PLUS_BUTTON_IMG, "Plus button"),
        (GAME_SKILLS_MENU_IMG, "Skills menu"),
    ]


def is_rejected_skill_queue_match(image_filename, location):
    try:
        screen_width, screen_height = pyautogui.size()
    except Exception:
        return False

    if image_filename == GAME_PLUS_BUTTON_IMG:
        if location.x < screen_width * 0.35 and location.y > screen_height * 0.58:
            log_event(
                f"Игнорируем ложный Plus button вне Skills window: ({location.x}, {location.y})."
            )
            return True

    if image_filename == GAME_SKILLS_MENU_IMG:
        if location.x < screen_width * 0.05 and location.y < screen_height * 0.08:
            log_event(
                f"Игнорируем ложный Skills menu в глобальном левом верхнем углу: ({location.x}, {location.y})."
            )
            return True

    return False


def find_skill_queue_image(image_options, confidence_level=0.75, logged_errors=None):
    for image_filename, image_description in image_options:
        image_path = str(resource_path(image_filename))
        try:
            matches = list(pyautogui.locateAllOnScreen(image_path, confidence=confidence_level))
            for match in matches:
                location = pyautogui.center(match)
                if is_rejected_skill_queue_match(image_filename, location):
                    continue
                log_image_match_diagnostic(image_filename, image_description, confidence_level, "found")
                return image_filename, image_description, location
        except Exception as e:
            error_text = str(e).strip()
            if error_text and logged_errors is not None and error_text not in logged_errors:
                log_event(f"ИСКЛЮЧЕНИЕ при skill queue поиске '{image_description}': {error_text}")
                logged_errors.add(error_text)
            if logged_errors is not None and "confidence" in error_text.lower() and "opencv" in error_text.lower():
                opencv_hint = "Для 'confidence' нужен OpenCV. Установи: pip install opencv-python"
                if opencv_hint not in logged_errors:
                    log_event(f">>> ВНИМАНИЕ: {opencv_hint}")
                    logged_errors.add(opencv_hint)
    return None, None, None


def wait_for_skill_queue_state(description, timeout_seconds=1, image_options=None):
    templates = image_options or skill_queue_state_templates()
    log_event(f"Проверяем skill queue состояние '{description}', таймаут: {timeout_seconds} сек...")
    start_time = time.time()
    logged_errors = set()
    while time.time() - start_time < timeout_seconds:
        image_filename, image_description, location = find_skill_queue_image(
            templates,
            confidence_level=0.75,
            logged_errors=logged_errors,
        )
        if location:
            log_event(f"Skill queue состояние '{description}' найдено: '{image_description}' ({image_filename}).")
            return image_filename, image_description, location
        time.sleep(PAUSE_SHORT)

    log_event(f"Skill queue состояние '{description}' не найдено.")
    return None, None, None


def click_on_skill_queue_image(image_filename, description, confidence_level=0.75, timeout_seconds=10):
    log_event(f"Ищем skill queue '{description}' (файл: {image_filename}, таймаут: {timeout_seconds} сек)...")
    start_time = time.time()
    logged_errors = set()
    while time.time() - start_time < timeout_seconds:
        _, image_description, location = find_skill_queue_image(
            [(image_filename, description)],
            confidence_level=confidence_level,
            logged_errors=logged_errors,
        )
        if location:
            human_click(location.x, location.y)
            log_event(f"Клик по skill queue '{image_description}' выполнен.")
            return True
        time.sleep(PAUSE_SHORT)

    log_image_match_diagnostic(image_filename, description, confidence_level, "timeout")
    log_event(f"ОШИБКА: skill queue '{description}' ({image_filename}) не найдено на экране.", important=True)
    return False


def click_skill_queue_image_until_state(
    image_filename,
    description,
    success_templates,
    success_description,
    confidence_level=0.75,
    click_timeout_seconds=10,
    verify_timeout_seconds=5,
    attempts=2,
):
    for attempt in range(1, attempts + 1):
        log_event(f"Попытка {attempt}/{attempts}: skill queue {description}.")
        if not click_on_skill_queue_image(
            image_filename,
            description,
            confidence_level=confidence_level,
            timeout_seconds=click_timeout_seconds,
        ):
            continue

        time.sleep(PAUSE_MEDIUM)
        found_image, found_description, _ = wait_for_skill_queue_state(
            success_description,
            timeout_seconds=verify_timeout_seconds,
            image_options=success_templates,
        )
        if found_image:
            log_event(f"Post-click проверка skill queue '{description}' успешна: найдено '{found_description}' ({found_image}).")
            return True

        log_event(
            f"Post-click проверка skill queue '{description}' не подтвердила состояние "
            f"'{success_description}'. Повторяем.",
            important=True,
        )

    log_event(
        f"ОШИБКА: skill queue '{description}' не привело к состоянию '{success_description}' "
        f"после {attempts} попыток.",
        important=True,
    )
    return False


def open_skills_window_for_queue():
    already_open_templates = [
        (GAME_SUCCESS_SKILL_IMG, "Skill queue import success"),
        (GAME_SKILL_QUEUE_REPLACE_BUTTON_IMG, "Replace skill queue"),
        (GAME_CONFIRM_BUTTON_IMG, "Confirm button"),
    ]
    after_click_templates = [
        (GAME_SUCCESS_SKILL_IMG, "Skill queue import success"),
        (GAME_SKILL_QUEUE_REPLACE_BUTTON_IMG, "Replace skill queue"),
        (GAME_CONFIRM_BUTTON_IMG, "Confirm button"),
        (GAME_SKILLS_MENU_IMG, "Skills menu"),
    ]
    for attempt in range(1, 5):
        image_filename, image_description, _ = wait_for_skill_queue_state(
            f"уже открытый Skills/skill queue state, попытка {attempt}",
            timeout_seconds=1,
            image_options=already_open_templates,
        )
        if image_filename:
            log_event(f"Skills UI уже в нужном состоянии: '{image_description}' ({image_filename}).")
            return image_filename

        if attempt > 1:
            click_optional_image(
                GAME_CLOSE_X2_IMG,
                "закрыть возможное перекрывающее окно перед Skills",
                confidence_level=0.75,
                timeout_seconds=1,
            )
            click_optional_image(
                GAME_CLOSE_X_IMG,
                "закрыть возможное окно перед Skills",
                confidence_level=0.75,
                timeout_seconds=1,
            )
            if attempt >= 3:
                pyautogui.press("esc")
                time.sleep(PAUSE_SHORT)

        if not focus_game_for_ui_action(f"Перед поиском Skills, попытка {attempt}"):
            continue

        log_event(f"Ищем и открываем Skills, попытка {attempt}/4.")
        if not click_on_first_found_image(
            [GAME_SKILLS_IMG, GAME_SKILLS_ALT_IMG],
            "Skills",
            confidence_level=0.75,
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        ):
            save_current_screenshot_evidence(f"skills_button_not_found_attempt_{attempt}")
            continue

        image_filename, image_description, _ = wait_for_skill_queue_state(
            "Skills state после клика Skills",
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
            image_options=after_click_templates,
        )
        if image_filename:
            log_event(f"Skills открыт: '{image_description}' ({image_filename}).")
            return image_filename

        save_current_screenshot_evidence(f"skills_state_not_found_after_click_attempt_{attempt}")

    log_event("ОШИБКА: Skills UI не найден и не открыт после повторных попыток.", important=True)
    return None


def press_alt_l_4_for_store():
    pyautogui.keyDown("alt")
    time.sleep(0.05)
    pyautogui.press("l")
    time.sleep(0.05)
    pyautogui.press("4")
    time.sleep(0.05)
    pyautogui.keyUp("alt")


def claim_omega_offer_from_store():
    log_event("--- Начало Omega store claim flow ---", important=True)
    if not focus_game_for_ui_action("Перед открытием магазина Omega"):
        return False

    log_event("Открываем магазин через Alt+L+4.")
    press_alt_l_4_for_store()

    if not click_image_until_state(
        GAME_OMEGA_STORE_ENTRY_IMG,
        "7 days Omega offer в Store",
        [(GAME_OMEGA_OFFER_IMG, "7 days Omega offer details")],
        "детальная страница 7 days Omega offer",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_STORE_LOAD,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=2,
    ):
        return False

    if not click_on_image(
        GAME_OMEGA_FREE_BUTTON_IMG,
        "Free button на 7 days Omega offer",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    log_event("Omega offer claimed, ждём заставку 2 сек и закрываем её Esc x2.")
    time.sleep(2)
    pyautogui.press("esc")
    time.sleep(1)
    pyautogui.press("esc")
    time.sleep(1)
    return True


def log_off_to_gift_claim_screen():
    log_event("--- Log Off после Omega claim ---", important=True)
    pyautogui.press("esc")
    time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)

    if not click_image_until_state(
        GAME_LOG_OFF_BUTTON_IMG,
        "Log Off",
        [(GAME_LOG_OFF_YES_BUTTON_IMG, "Log Off confirmation Yes")],
        "подтверждение Log Off",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_QUIT_MENU_READY,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=2,
    ):
        return False

    if not click_on_image(
        GAME_LOG_OFF_YES_BUTTON_IMG,
        "Yes на подтверждении Log Off",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    image_filename, image_description, _ = wait_for_optional_image(
        [(GAME_GIFT_CLAIM_BUTTON_IMG, "Gift claim button")],
        "Gift claim после Log Off",
        timeout_seconds=TIMEOUT_GAME_GIFT_CLAIM,
        confidence_level=0.75,
    )
    if not image_filename:
        return False

    log_event(f"Gift claim screen подтверждён: '{image_description}' ({image_filename}).")
    return True


def claim_gift_and_reenter_character():
    if not click_on_image(
        GAME_GIFT_CLAIM_BUTTON_IMG,
        "Gift claim button",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    time.sleep(1)
    pyautogui.press("esc")
    time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)

    if not click_on_image(
        GAME_CHARACTER_PICK_IMG,
        "Character pick после Gift Claim",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_CHARACTER_PICK,
    ):
        return False

    if not wait_for_game_ready_for_input(timeout_seconds=TIMEOUT_GAME_READY_FOR_INPUT):
        return False

    close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_QUICK_SCAN)
    return True


def redeem_pending_gifts_to_station():
    log_event("--- Начало redeem gifts flow ---", important=True)
    if not click_first_image_until_state(
        [
            (GAME_GIFTS_BUTTON_IMG, "Gifts button"),
            (GAME_GIFTS_BUTTON_ALT_IMG, "Gifts button alternate"),
        ],
        "Gifts button",
        [(GAME_REDEEM_TO_CURRENT_STATION_IMG, "Redeem to current station")],
        "окно Gifts с Redeem to current station",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=2,
    ):
        return False

    if not click_image_until_state(
        GAME_REDEEM_TO_CURRENT_STATION_IMG,
        "Redeem to current station",
        [(GAME_REDEEM_YES_BUTTON_IMG, "Redeem yes")],
        "подтверждение Redeem",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=2,
    ):
        return False

    if not click_on_image(
        GAME_REDEEM_YES_BUTTON_IMG,
        "Yes на подтверждении Redeem",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    time.sleep(PAUSE_MEDIUM)
    if wait_for_optional_image(
        [(GAME_EXPERT_SYSTEM_EVENT_IMG, "Expert system event")],
        "Expert System event после Redeem",
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
        confidence_level=0.75,
    )[0]:
        click_optional_image(
            GAME_CLOSE_X2_IMG,
            "закрыть Expert System event",
            confidence_level=0.75,
            timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
        )

    return True


def import_omega_skill_queue():
    log_event("--- Начало импорта skills2.txt в skill queue ---", important=True)
    skills_text = read_required_text_file(OMEGA_SKILLS_FILE_PATH, "Omega skill queue file")
    if not skills_text:
        return False

    state_image = open_skills_window_for_queue()
    if not state_image:
        return False

    if state_image not in {GAME_SUCCESS_SKILL_IMG, GAME_PLUS_BUTTON_IMG}:
        if not set_text_for_proton_clipboard(skills_text):
            return False

        if state_image != GAME_SKILL_QUEUE_REPLACE_BUTTON_IMG:
            if not click_skill_queue_image_until_state(
                GAME_SKILLS_MENU_IMG,
                "Skills menu",
                [(GAME_SKILL_QUEUE_REPLACE_BUTTON_IMG, "Replace skill queue")],
                "Replace skill queue button",
                confidence_level=0.75,
                click_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
                verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
                attempts=2,
            ):
                return False

        if not click_skill_queue_image_until_state(
            GAME_SKILL_QUEUE_REPLACE_BUTTON_IMG,
            "Replace skill queue",
            [(GAME_SUCCESS_SKILL_IMG, "Skill queue import success"), (GAME_PLUS_BUTTON_IMG, "Plus button")],
            "Skill queue import success",
            confidence_level=0.75,
            click_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
            verify_timeout_seconds=TIMEOUT_GAME_SKILL_QUEUE_SUCCESS,
            attempts=2,
        ):
            return False
    else:
        log_event("Skill queue уже выглядит импортированным, продолжаем с Plus/Confirm.")

    click_optional_image(
        GAME_CLOSE3_IMG,
        "закрыть popup успешного импорта skill queue",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
    )

    if not click_skill_queue_image_until_state(
        GAME_PLUS_BUTTON_IMG,
        "Plus button после успешного импорта skill queue",
        [(GAME_CONFIRM_BUTTON_IMG, "Confirm button")],
        "Confirm после Plus",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=3,
    ):
        return False

    if not click_on_skill_queue_image(
        GAME_CONFIRM_BUTTON_IMG,
        "Confirm после Plus",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    time.sleep(1)
    if not click_on_first_found_image(
        [GAME_CLOSE1_IMG, GAME_CLOSE2_IMG],
        "Close после подтверждения skill queue",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    pyautogui.press("esc")
    time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)
    return True


def perform_omega_gifts_and_skill_queue_flow():
    if not claim_omega_offer_from_store():
        log_event("ОШИБКА: Omega store claim flow не завершён.", important=True)
        return False
    if not log_off_to_gift_claim_screen():
        log_event("ОШИБКА: Log Off до gift claim screen не завершён.", important=True)
        return False
    if not claim_gift_and_reenter_character():
        log_event("ОШИБКА: Gift claim / character pick flow не завершён.", important=True)
        return False
    if not redeem_pending_gifts_to_station():
        log_event("ОШИБКА: Redeem gifts flow не завершён.", important=True)
        return False
    if not import_omega_skill_queue():
        log_event("ОШИБКА: импорт Omega skill queue не завершён.", important=True)
        return False

    log_event("Omega/gifts/skill queue flow успешно завершён.", important=True)
    return True


def extract_skill_from_row(skill_image, skill_description):
    if not right_click_skill_row_best_match(
        skill_image,
        skill_description,
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    time.sleep(PAUSE_SHORT)
    if not click_on_image_best_match(
        GAME_EXTRACT_SKILL_BUTTON_IMG,
        "Extract Skill",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    time.sleep(PAUSE_MEDIUM)
    return True


def locate_image_match_for_action(image_filename, description, confidence_level=0.75, timeout_seconds=10):
    template_path = resource_path(image_filename)
    start_time = time.time()
    last_error = None
    while time.time() - start_time < timeout_seconds:
        try:
            import cv2
            import numpy as np
            from PIL import Image

            screenshot = pyautogui.screenshot().convert("RGB")
            template = Image.open(template_path).convert("RGB")
            template_width, template_height = template.size
            result = cv2.matchTemplate(
                np.array(screenshot),
                np.array(template),
                cv2.TM_CCOEFF_NORMED,
            )
            _, max_value, _, max_location = cv2.minMaxLoc(result)
            if max_value >= confidence_level:
                log_image_match_diagnostic(image_filename, description, confidence_level, "found")
                center_x = int(max_location[0] + template_width / 2)
                center_y = int(max_location[1] + template_height / 2)
                match = {
                    "score": float(max_value),
                    "x": int(max_location[0]),
                    "y": int(max_location[1]),
                    "width": template_width,
                    "height": template_height,
                    "center_x": center_x,
                    "center_y": center_y,
                }
                log_event(
                    f"Best-match '{description}' найден: score={match['score'] * 100:.1f}% "
                    f"center=({center_x}, {center_y})."
                )
                return match
            time.sleep(PAUSE_SHORT)
        except Exception as e:
            error_text = str(e).strip()
            if error_text and error_text != last_error:
                log_event(f"ИСКЛЮЧЕНИЕ при поиске '{description}': {error_text}")
                last_error = error_text
            time.sleep(PAUSE_SHORT)

    log_image_match_diagnostic(image_filename, description, confidence_level, "timeout")
    log_event(f"ОШИБКА: '{description}' ({image_filename}) не найдено для действия.", important=True)
    return None


def locate_image_center_for_action(image_filename, description, confidence_level=0.75, timeout_seconds=10):
    match = locate_image_match_for_action(
        image_filename,
        description,
        confidence_level=confidence_level,
        timeout_seconds=timeout_seconds,
    )
    if not match:
        return None
    return match["center_x"], match["center_y"]


def right_click_skill_row_best_match(skill_image, skill_description, confidence_level=0.75, timeout_seconds=10):
    log_event(
        f"Ищем best-match строки skill '{skill_description}' для right-click "
        f"(файл: {skill_image}, таймаут: {timeout_seconds} сек)..."
    )
    skill_match = locate_image_match_for_action(
        skill_image,
        skill_description,
        confidence_level=confidence_level,
        timeout_seconds=timeout_seconds,
    )
    if not skill_match:
        return False

    if skill_match["x"] > 1150:
        click_x = skill_match["x"] - 65
    else:
        click_x = skill_match["x"] + 5
    click_y = skill_match["center_y"]

    pyautogui.moveTo(click_x, click_y, duration=0.14 + random.uniform(0, 0.12))
    pyautogui.click(click_x, click_y, button="right")
    log_event(
        f"right-click по строке skill '{skill_description}' выполнен в ({click_x}, {click_y}); "
        f"text_match_center=({skill_match['center_x']}, {skill_match['center_y']})."
    )
    return True


def click_on_image_best_match(
    image_filename,
    description,
    confidence_level=0.8,
    timeout_seconds=10,
    button="left",
    clicks=1,
    interval=0.1,
):
    log_event(
        f"Ищем best-match '{description}' для {button}-click x{clicks} "
        f"(файл: {image_filename}, таймаут: {timeout_seconds} сек)..."
    )
    location = locate_image_center_for_action(
        image_filename,
        description,
        confidence_level=confidence_level,
        timeout_seconds=timeout_seconds,
    )
    if not location:
        return False

    x, y = location
    pyautogui.moveTo(x, y, duration=0.14 + random.uniform(0, 0.12))
    pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
    log_event(f"{button}-click x{clicks} по best-match '{description}' выполнен в ({x}, {y}).")
    return True


def prepare_active_skill_extractor_window():
    image_filename, image_description, location = wait_for_optional_image(
        [
            (GAME_LEAVE_CURRENT_SHIP_BUTTON_IMG, "Leave Current Ship"),
            (GAME_SKILLS_ENGINEERING_IMG, "Engineering в окне Skill Extractor"),
        ],
        "окно Skill Extractor или prompt Leave Current Ship",
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        confidence_level=0.75,
    )
    if not image_filename:
        save_current_screenshot_evidence("skill_extractor_window_not_ready")
        return False

    if image_filename == GAME_LEAVE_CURRENT_SHIP_BUTTON_IMG:
        human_click(location.x, location.y)
        log_event(f"Клик по '{image_description}' выполнен перед Skill Extractor.")
        time.sleep(PAUSE_MEDIUM)
        if not wait_for_optional_image(
            [(GAME_SKILLS_ENGINEERING_IMG, "Engineering в окне Skill Extractor")],
            "окно Skill Extractor после Leave Current Ship",
            timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
            confidence_level=0.75,
        )[0]:
            save_current_screenshot_evidence("skill_extractor_after_leave_ship_not_ready")
            return False

    return True


def open_engineering_in_skill_extractor(expected_skill_image=GAME_SKILL_ELECTRONIC_UPGRADES_IMG, expected_skill_description="Electronic Upgrades"):
    if wait_for_optional_image(
        [(expected_skill_image, expected_skill_description)],
        f"{expected_skill_description} уже виден",
        timeout_seconds=1,
        confidence_level=0.75,
    )[0]:
        return True

    return click_image_until_state(
        GAME_SKILLS_ENGINEERING_IMG,
        "Engineering в окне Skill Extractor",
        [(expected_skill_image, expected_skill_description)],
        f"{expected_skill_description} после открытия Engineering",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=3,
    )


def perform_active_skill_extractor_flow(skill_rows, flow_description):
    log_event(f"--- Начало выбора skills для извлечения SP: {flow_description} ---", important=True)
    first_skill_image, first_skill_description = skill_rows[0]

    if not open_engineering_in_skill_extractor(first_skill_image, first_skill_description):
        return False

    for skill_image, skill_description in skill_rows:
        if not extract_skill_from_row(skill_image, skill_description):
            return False

    if not click_on_image_best_match(
        GAME_BIG_EXTRACT_BUTTON_IMG,
        "большая кнопка Extract",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    time.sleep(PAUSE_MEDIUM)
    click_optional_image(
        GAME_CLOSE3_IMG,
        "закрыть окно после большого Extract",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
    )

    selected_descriptions = ", ".join(skill_description for _, skill_description in skill_rows)
    log_event(f"Skill Extractor flow успешен: выбраны {selected_descriptions}, нажата большая Extract.", important=True)
    return True


def activate_skill_extractor_and_extract(skill_rows, flow_description):
    if not ensure_inventory_item_available(
        GAME_SKILL_EXTRACTOR_IMG,
        "Skill Extractor",
        flow_description,
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

    if not prepare_active_skill_extractor_window():
        log_event("ОШИБКА: окно Skill Extractor не подтвердилось после Activate Skill Extractor.", important=True)
        return False

    if not perform_active_skill_extractor_flow(skill_rows, flow_description):
        log_event(f"ОШИБКА: Skill Extractor flow не завершён: {flow_description}.", important=True)
        return False

    return True


def inventory_item_already_visible(item_image, item_description, context_description, timeout_seconds=1):
    image_filename, image_description, _ = wait_for_optional_image(
        [(item_image, item_description)],
        f"{item_description} уже виден ({context_description})",
        timeout_seconds=timeout_seconds,
        confidence_level=0.75,
    )
    if image_filename:
        log_event(
            f"{image_description} уже виден ({context_description}); Jita 4 не нажимаем."
        )
        return True
    return False


def open_inventory_jita4(context_description, target_image=None, target_description=None):
    if target_image and inventory_item_already_visible(
        target_image,
        target_description,
        context_description,
    ):
        return True

    if not click_on_image(
        GAME_INVENTORY_ICON_IMG,
        f"Inventory ({context_description})",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    if target_image and inventory_item_already_visible(
        target_image,
        target_description,
        context_description,
    ):
        return True

    if not click_on_image(
        GAME_JITA4_IMG,
        f"Jita 4 в inventory ({context_description})",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    return True


def select_jita4_for_existing_or_new_inventory(context_description, target_image=None, target_description=None):
    if target_image and inventory_item_already_visible(
        target_image,
        target_description,
        context_description,
    ):
        return True

    if click_on_image(
        GAME_JITA4_IMG,
        f"Jita 4 в уже открытом inventory ({context_description})",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
    ):
        return True

    log_event(f"Jita 4 не найден в уже открытом окне ({context_description}); открываем Inventory.")
    return open_inventory_jita4(context_description, target_image, target_description)


def ensure_inventory_item_available(item_image, item_description, context_description):
    if inventory_item_already_visible(
        item_image,
        item_description,
        context_description,
    ):
        return True

    if not select_jita4_for_existing_or_new_inventory(
        context_description,
        target_image=item_image,
        target_description=item_description,
    ):
        return False

    if inventory_item_already_visible(
        item_image,
        item_description,
        context_description,
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
    ):
        return True

    log_event(
        f"{item_description} не подтвердился сразу после выбора Jita 4 ({context_description}); "
        "продолжаем, следующий обязательный image-click выполнит финальную проверку.",
        important=True,
    )
    return True


def perform_contract_and_extractor_flow(current_username):
    log_event(f"--- Начало contract/extractor flow для {current_username} ---", important=True)

    if not open_game_left_menu_and_click_finance():
        log_event("ОШИБКА: не удалось открыть Finance через левое меню игры.", important=True)
        return False

    if not open_contracts_section():
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
        GAME_CLOSE3_IMG,
        "закрыть окно принятия контракта",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_OPTIONAL_ACTION,
    )
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

    if not activate_skill_extractor_and_extract(
        [
            (GAME_SKILL_ELECTRONIC_UPGRADES_IMG, "Electronic Upgrades"),
            (GAME_SKILL_CPU_MANAGEMENT_IMG, "CPU Management"),
        ],
        "первый extractor",
    ):
        return False

    log_event("После первого extractor повторно не открываем Inventory/Jita; используем уже открытое окно assets.")
    if not activate_skill_extractor_and_extract(
        [
            (GAME_SKILL_WEAPON_UPGRADES_IMG, "Weapon Upgrades"),
            (GAME_SKILL_CPU_MANAGEMENT_IMG, "CPU Management"),
        ],
        "второй extractor",
    ):
        return False

    log_event("Contract/extractor flow успешен: оба extractor применены к выбранным skills.", important=True)
    return True


def log_off_to_isk_claim_screen():
    log_event("--- Log Off перед финальным claim 10 000 ISK ---", important=True)
    pyautogui.press("esc")
    time.sleep(PAUSE_AFTER_INGAME_ESC_PRESS)

    if not click_image_until_state(
        GAME_LOG_OFF_BUTTON_IMG,
        "Log Off перед финальным claim",
        [(GAME_LOG_OFF_YES_BUTTON_IMG, "Log Off confirmation Yes")],
        "подтверждение Log Off перед финальным claim",
        confidence_level=0.75,
        click_timeout_seconds=TIMEOUT_GAME_QUIT_MENU_READY,
        verify_timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        attempts=2,
    ):
        return False

    if not click_on_image(
        GAME_LOG_OFF_YES_BUTTON_IMG,
        "Yes на подтверждении финального Log Off",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    image_filename, image_description, _ = wait_for_optional_image(
        [(GAME_CLAIM_BUTTON_IMG, "10 000 ISK claim button")],
        "10 000 ISK claim после финального Log Off",
        timeout_seconds=TIMEOUT_GAME_GIFT_CLAIM,
        confidence_level=0.75,
    )
    if not image_filename:
        return False

    log_event(f"Финальный claim screen подтверждён: '{image_description}' ({image_filename}).")
    return True


def claim_isk_and_reenter_character():
    if not click_on_image(
        GAME_CLAIM_BUTTON_IMG,
        "10 000 ISK claim button",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    time.sleep(1)
    click_optional_image(
        GAME_CLOSE3_IMG,
        "закрыть окно после 10 000 ISK claim",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    )

    if not click_on_image(
        GAME_CHARACTER_PICK_IMG,
        "Character pick после финального claim",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_CHARACTER_PICK,
    ):
        return False

    if not wait_for_game_ready_for_input(timeout_seconds=TIMEOUT_GAME_READY_FOR_INPUT):
        return False

    close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_QUICK_SCAN)
    return True


def select_exact_phrase_contract_search():
    log_event("Ищем Search By и выбираем Only Exact Phrase относительным кликом в dropdown.")
    match = locate_image_match_for_action(
        GAME_SEARCH_BY_IMG,
        "Search By label",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    )
    if not match:
        return False

    click_x = match["x"] + match["width"] + CONTRACT_SEARCH_BY_DROPDOWN_X_OFFSET
    click_y = match["center_y"]
    human_click(click_x, click_y)
    log_event(
        f"Клик справа от Search By выполнен в ({click_x}, {click_y}); "
        f"search_by_match=({match['x']}, {match['y']}, {match['width']}x{match['height']})."
    )
    time.sleep(CONTRACT_SEARCH_DROPDOWN_PAUSE_SECONDS)

    option_click_x = click_x
    option_click_y = click_y + CONTRACT_ONLY_EXACT_PHRASE_DROPDOWN_Y_OFFSET
    human_click(option_click_x, option_click_y)
    log_event(
        f"Клик по Only Exact Phrase выполнен относительной точкой "
        f"({option_click_x}, {option_click_y}); base=({click_x}, {click_y}), "
        f"y_offset={CONTRACT_ONLY_EXACT_PHRASE_DROPDOWN_Y_OFFSET}."
    )
    time.sleep(PAUSE_MEDIUM)

    return True


def click_contract_type_checkbox():
    log_event("Ищем Type checkbox и кликаем именно по квадрату рядом с Type.")
    match = locate_image_match_for_action(
        GAME_TYPE_BOX_IMG,
        "Type checkbox",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    )
    if not match:
        return False

    click_x = match["x"] + 8
    click_y = match["center_y"]
    human_click(click_x, click_y)
    log_event(
        f"Клик по квадрату Type выполнен в ({click_x}, {click_y}); "
        f"type_box_match=({match['x']}, {match['y']}, {match['width']}x{match['height']})."
    )
    time.sleep(PAUSE_MEDIUM)
    return True


def click_contract_next(step_number):
    if not click_on_image(
        GAME_NEXT_BUTTON_IMG,
        f"Next в contract wizard #{step_number}",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False
    time.sleep(PAUSE_MEDIUM)
    return True


def finish_large_skill_injector_contract_from_exact_phrase_stage():
    log_event("--- Продолжение Large Skill Injector contract с этапа Exact Phrase ---", important=True)

    type_box_visible = wait_for_optional_image(
        [(GAME_TYPE_BOX_IMG, "Type checkbox")],
        "Type checkbox перед выбором Exact Phrase",
        timeout_seconds=1,
        confidence_level=0.75,
    )[0]
    if type_box_visible:
        log_event("Type checkbox уже виден: считаем, что первый Next уже выполнен, продолжаем с выбора Type.")
    else:
        if not select_exact_phrase_contract_search():
            return False
        if not click_contract_next(1):
            return False

    if not click_contract_type_checkbox():
        return False

    for step_number in range(2, 4):
        if not click_contract_next(step_number):
            return False

    if not click_on_image(
        GAME_FINISH_BUTTON_IMG,
        "Finish contract",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    if not click_on_image(
        GAME_YES_BUTTON_IMG,
        "Yes на подтверждении создания контракта",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    image_filename, image_description, _ = wait_for_optional_image(
        [(GAME_SUCCESS_SCREEN_IMG, "success_screen")],
        "success_screen после создания контракта",
        timeout_seconds=TIMEOUT_GAME_REQUIRED_STATE,
        confidence_level=0.75,
    )
    if not image_filename:
        return False

    log_event(f"Финальный contract flow подтверждён: '{image_description}' ({image_filename}).", important=True)
    if not click_on_image(
        GAME_CLOSE3_IMG,
        "закрыть success_screen",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    return True


def create_large_skill_injector_contract():
    log_event("--- Начало создания private contract с Large Skill Injector ---", important=True)

    if not focus_game_for_ui_action("Перед созданием контракта Large Skill Injector"):
        return False

    if not ensure_inventory_item_available(
        GAME_LARGE_SKILL_INJECTOR_IMG,
        "Large Skill Injector",
        "для Large Skill Injector",
    ):
        return False

    if not click_on_image_custom(
        GAME_LARGE_SKILL_INJECTOR_IMG,
        "Large Skill Injector",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
        button="right",
    ):
        return False

    if not click_on_image(
        GAME_CREATE_CONTRACT_IMG,
        "Create Contract для Large Skill Injector",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    if not click_on_image(
        GAME_PRIVATE_IMG,
        "Private contract",
        confidence_level=0.75,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    if not type_text_into_image_field(
        GAME_NAME_FIELD_IMG,
        "поле имени получателя контракта",
        "Chabiad",
        interval=0.08,
        timeout_seconds=TIMEOUT_GAME_REQUIRED_ACTION,
    ):
        return False

    return finish_large_skill_injector_contract_from_exact_phrase_stage()


def perform_final_large_skill_injector_contract_flow():
    log_event("--- Начало финального flow: claim, redeem gifts, contract Large Skill Injector ---", important=True)

    if not log_off_to_isk_claim_screen():
        log_event("ОШИБКА: финальный Log Off до 10 000 ISK claim не завершён.", important=True)
        return False
    if not claim_isk_and_reenter_character():
        log_event("ОШИБКА: финальный claim / character pick flow не завершён.", important=True)
        return False
    if not redeem_pending_gifts_to_station():
        log_event("ОШИБКА: финальный Redeem gifts flow не завершён.", important=True)
        return False
    if not create_large_skill_injector_contract():
        log_event("ОШИБКА: private contract с Large Skill Injector не создан.", important=True)
        return False

    log_event("Финальный flow успешно завершён: Large Skill Injector contract создан.", important=True)
    return True


def wait_for_no_game_processes(timeout_seconds):
    start_time = time.time()
    last_logged_remaining = None
    while time.time() - start_time < timeout_seconds:
        remaining_processes = sorted(get_game_process_ids())
        if not remaining_processes:
            return True
        if remaining_processes != last_logged_remaining:
            log_event(f"Ожидаем завершение game client процессов: {remaining_processes}.")
            last_logged_remaining = remaining_processes
        time.sleep(PAUSE_SHORT)
    return not get_game_process_ids()


def force_close_game_client(reason):
    pids = sorted(get_game_process_ids())
    if not pids:
        log_event(f"Force-close game client не требуется: game process уже не найден ({reason}).", important=True)
        return True

    log_event(f"Force-close game client после неудачного штатного выхода: {reason}; PIDs={pids}.", important=True)
    for sig, sig_name, timeout_seconds in (
        (signal.SIGTERM, "SIGTERM", PAUSE_FOR_GAME_TO_CLOSE),
        (signal.SIGKILL, "SIGKILL", PAUSE_FOR_GAME_TO_CLOSE_EMERGENCY),
    ):
        current_pids = sorted(get_game_process_ids())
        if not current_pids:
            log_event("Game client завершён перед отправкой следующего сигнала.", important=True)
            return True

        for pid in current_pids:
            try:
                os.kill(pid, sig)
                log_event(f"Отправлен {sig_name} game client PID {pid}.")
            except ProcessLookupError:
                log_event(f"Game client PID {pid} уже завершился до {sig_name}.")
            except PermissionError as exc:
                log_event(f"Нет прав отправить {sig_name} game client PID {pid}: {exc}", important=True)
            except OSError as exc:
                log_event(f"Ошибка при отправке {sig_name} game client PID {pid}: {exc}", important=True)

        if wait_for_no_game_processes(timeout_seconds):
            log_event(f"Game client завершён после {sig_name}.", important=True)
            return True

    remaining = sorted(get_game_process_ids())
    log_event(f"ОШИБКА: force-close game client не завершил процессы: {remaining}.", important=True)
    return False


def finish_game_exit_with_optional_force_kill(allow_force_kill, reason):
    if not allow_force_kill:
        return False

    if not force_close_game_client(reason):
        return False

    if wait_for_launcher_visible_optional(
        "лаунчер после force-close game client",
        timeout_seconds=TIMEOUT_LAUNCHER_ACCOUNT_REMOVAL_READY,
    ):
        log_event("Лаунчер виден после force-close game client.", important=True)
    else:
        log_event(
            "Лаунчер не подтверждён сразу после force-close game client; "
            "следующий launcher-шаг попробует восстановить окно.",
            important=True,
        )
    return True


def quit_game_to_launcher(game_process_baseline, allow_force_kill=False):
    log_event("--- Начало выхода из игры через Esc + Quit Game ---", important=True)

    if wait_for_game_closed_confirmation(game_process_baseline, timeout_seconds=2):
        log_event("Игра уже закрыта и лаунчер виден. Esc + Quit Game не требуется.", important=True)
        return True
    if allow_force_kill and not get_game_process_ids():
        log_event(
            "Game process уже не найден, но лаунчер не подтвердился. "
            "После успешного финального flow продолжаем к launcher recovery.",
            important=True,
        )
        return True

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
            if allow_force_kill:
                log_event(
                    "После Quit Game закрытие клиента/восстановление лаунчера не подтвердилось. "
                    "После успешного финального flow пробуем force-close game client.",
                    important=True,
                )
            else:
                log_event("После Quit Game закрытие клиента/восстановление лаунчера не подтвердилось. Останавливаемся без удаления аккаунта.", important=True)
            return finish_game_exit_with_optional_force_kill(
                allow_force_kill,
                "Quit Game нажали, но закрытие/launcher confirmation не подтвердились",
            )

        close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_QUICK_SCAN)

    log_event("ОШИБКА: кнопка Quit Game не найдена после Esc. Выход из игры не подтверждён.", important=True)
    return finish_game_exit_with_optional_force_kill(
        allow_force_kill,
        "кнопка Quit Game не найдена после Esc",
    )


def process_logged_in_game_session(current_username, game_process_baseline):
    log_event(f"--- Начало игровой сессии для {current_username}: Omega/gifts/skills, extractor, final contract и выход ---", important=True)
    close_optional_game_popups(timeout_seconds=TIMEOUT_GAME_POPUP_SCAN)
    if not perform_omega_gifts_and_skill_queue_flow():
        log_event("Обязательный Omega/gifts/skill queue flow не подтверждён. Пробуем штатно выйти, но аккаунт удалять нельзя.", important=True)
        if quit_game_to_launcher(game_process_baseline):
            log_event("Игра закрыта штатно, но Omega/gifts/skill queue flow не выполнен. Аккаунт не удаляем.", important=True)
        else:
            log_event("Omega/gifts/skill queue flow не выполнен, и выход из игры не подтверждён.", important=True)
        return False

    if not perform_contract_and_extractor_flow(current_username):
        log_event("Обязательный contract/extractor flow не подтверждён. Пробуем штатно выйти, но аккаунт удалять нельзя.", important=True)
        if quit_game_to_launcher(game_process_baseline):
            log_event("Игра закрыта штатно, но contract/extractor flow не выполнен. Аккаунт не удаляем.", important=True)
        else:
            log_event("Contract/extractor flow не выполнен, и выход из игры не подтверждён.", important=True)
        return False

    if not perform_final_large_skill_injector_contract_flow():
        log_event("Обязательный финальный Large Skill Injector contract flow не подтверждён. Пробуем штатно выйти, но аккаунт удалять нельзя.", important=True)
        if quit_game_to_launcher(game_process_baseline):
            log_event("Игра закрыта штатно, но финальный Large Skill Injector contract flow не выполнен. Аккаунт не удаляем.", important=True)
        else:
            log_event("Финальный Large Skill Injector contract flow не выполнен, и выход из игры не подтверждён.", important=True)
        return False

    if not quit_game_to_launcher(game_process_baseline, allow_force_kill=True):
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
    if recover_existing_launcher_visibility("лаунчер перед удалением аккаунта", force_focus=True):
        return True

    log_event("Лаунчер перед удалением аккаунта не подтверждён с фокусом. Удаление аккаунта запрещено.", important=True)
    return False


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

    if not click_launcher_image_until_state(
        LAUNCHER_ACCOUNT_SETTINGS_IMG,
        "Account Settings",
        [(LAUNCHER_REMOVE_ACCOUNT_BUTTON_IMG, "Remove Account")],
        "меню Account Settings с Remove Account",
        confidence_level=0.75,
        click_timeout_seconds=10,
        verify_timeout_seconds=6,
    ):
        return False
    if not click_launcher_image_until_state(
        LAUNCHER_REMOVE_ACCOUNT_BUTTON_IMG,
        "Remove Account",
        [(LAUNCHER_CONFIRM_REMOVE_BUTTON_IMG, "Confirm Remove Account")],
        "подтверждение Remove Account",
        confidence_level=0.75,
        click_timeout_seconds=10,
        verify_timeout_seconds=6,
    ):
        return False
    if not click_launcher_image_until_disappears(
        LAUNCHER_CONFIRM_REMOVE_BUTTON_IMG,
        "Confirm Remove Account",
        confidence_level=0.75,
        click_timeout_seconds=10,
        disappear_timeout_seconds=15,
    ):
        return False
    log_event(f"Аккаунт {current_username} удален из лаунчера.")
    return True


def retry_account_removal_after_launcher_restart(current_username, reason):
    log_event(
        f"Удаление аккаунта {current_username} не подтвердилось. "
        "Перезапускаем лаунчер и первым действием повторяем удаление этого же аккаунта.",
        important=True,
    )
    force_cleanup_eve_processes(f"account removal retry after launcher focus failure: {reason}")
    time.sleep(PAUSE_BETWEEN_ACCOUNTS_PROCESSING)

    if not start_initial_launcher():
        log_event("ОШИБКА: не удалось перезапустить лаунчер для повторного удаления аккаунта.", important=True)
        return False

    time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC)
    if remove_account_from_launcher(current_username):
        log_event(f"Аккаунт {current_username} удалён после перезапуска лаунчера.", important=True)
        return True

    log_event(f"Повторное удаление аккаунта {current_username} после перезапуска лаунчера не подтвердилось.", important=True)
    return False


def latest_failure_reason_for_account(account_number, default_reason):
    for failed_account_number, reason in reversed(failed_accounts_details):
        if failed_account_number == account_number:
            return reason
    return default_reason


def append_failed_account_runtime_log(account_number, username, reason, observed_state, consecutive_failures):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = (
        f"{timestamp} | account={account_number} | username={username} | "
        f"consecutive_failures={consecutive_failures} | reason={reason} | observed={observed_state}\n"
    )
    try:
        with open(resource_path(FAILED_ACCOUNTS_LOG_FILE_PATH), "a", encoding="utf-8") as failed_log:
            failed_log.write(log_line)
    except Exception as exc:
        log_event(f"Не удалось записать failed-account log: {type(exc).__name__}: {exc}", important=True)


def diagnose_account_failure_state():
    if not ACCOUNT_FAILURE_DIAGNOSTICS:
        return "diagnostics disabled"

    checks = [
        ("login dialog", login_dialog_templates()),
        ("email verification", email_verification_templates()),
        ("game ready", game_ready_templates()),
        ("omega store", omega_store_templates()),
        ("gifts", gift_redeem_templates()),
        ("skill queue", skill_queue_templates()),
        ("game menu", [(GAME_FINANCE_BUTTON_IMG, "Finance button"), (GAME_MENU_BUTTON_IMG, "Game menu button")]),
        ("contracts", [(GAME_MY_CONTRACTS_BUTTON_IMG, "My Contracts"), (GAME_CONTRACT_NAME_BUTTON_IMG, "Contract name")]),
        ("skill extraction", skill_extraction_progress_templates()),
        ("extractor result", extractor_success_templates()),
        ("final injector contract", final_large_skill_injector_contract_templates()),
        ("launcher", launcher_visibility_templates()),
    ]

    logged_errors = set()
    for state_name, templates in checks:
        image_filename, image_description, _ = find_first_available_image(
            templates,
            confidence_level=0.75,
            logged_errors=logged_errors,
        )
        if image_filename:
            observed_state = f"{state_name}: {image_description} ({image_filename})"
            log_event(f"Диагностика сбоя: видимое состояние: {observed_state}", important=True)
            return observed_state

    game_processes = sorted(get_game_process_ids())
    if game_processes:
        observed_state = f"game process still running: {game_processes}"
    else:
        observed_state = "known UI not detected; game process not found"
    log_event(f"Диагностика сбоя: {observed_state}", important=True)
    return observed_state


def force_cleanup_eve_processes(reason):
    if not FORCE_CLEANUP_PROCESS_PATTERNS:
        log_event("Fail-soft cleanup пропущен: EVE_FORCE_CLEANUP_PROCESS_PATTERNS пустой.")
        return

    log_event(f"Fail-soft cleanup процессов EVE после сбоя: {reason}", important=True)
    if shutil.which("pkill") is None:
        log_event("pkill не найден в PATH, cleanup процессов EVE недоступен.", important=True)
        return

    for pattern in FORCE_CLEANUP_PROCESS_PATTERNS:
        try:
            result = subprocess.run(
                ["pkill", "-fi", pattern],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
        except Exception as exc:
            log_event(f"pkill для pattern '{pattern}' не выполнен: {type(exc).__name__}: {exc}", important=True)
            continue

        if result.returncode == 0:
            log_event(f"pkill завершил процессы по pattern '{pattern}'.")
        elif result.returncode == 1:
            log_event(f"pkill не нашёл процессы по pattern '{pattern}'.")
        else:
            error_text = result.stderr.strip()
            log_event(f"pkill вернул код {result.returncode} для pattern '{pattern}': {error_text}", important=True)


def record_account_failure(account_number, username, reason, cleanup_processes=True, append_detail=True):
    global consecutive_registration_failures, total_registration_failures
    global script_should_terminate, termination_reason_str, last_account_for_termination

    if append_detail and account_number not in [acc_num for acc_num, _ in failed_accounts_details]:
        failed_accounts_details.append((account_number, reason))

    total_registration_failures += 1
    consecutive_registration_failures += 1

    log_event(
        f"Аккаунт {username} помечен как неудачный: {reason}. "
        f"Подряд: {consecutive_registration_failures}/{MAX_CONSECUTIVE_ACCOUNT_FAILURES}.",
        important=True,
    )
    save_current_screenshot_evidence(f"account_{account_number}_failure")
    observed_state = diagnose_account_failure_state()
    append_failed_account_runtime_log(
        account_number,
        username,
        reason,
        observed_state,
        consecutive_registration_failures,
    )

    if cleanup_processes:
        force_cleanup_eve_processes(reason)

    if not FAIL_SOFT_ACCOUNTS:
        script_should_terminate = True
        termination_reason_str = f"Аккаунт {username} завершился ошибкой, fail-soft отключён: {reason}"
        last_account_for_termination = account_number
        return False

    max_failures = max(1, MAX_CONSECUTIVE_ACCOUNT_FAILURES)
    if consecutive_registration_failures >= max_failures:
        script_should_terminate = True
        termination_reason_str = f"Остановлено: {consecutive_registration_failures} неудачных аккаунтов подряд."
        last_account_for_termination = account_number
        return False

    return True


def advance_to_next_account_after_failure(account_number, username, reason, append_detail=True):
    global script_should_terminate, termination_reason_str, last_account_for_termination

    if not record_account_failure(
        account_number,
        username,
        reason,
        cleanup_processes=True,
        append_detail=append_detail,
    ):
        return None

    next_account_number = account_number + 1
    if next_account_number > END_ACCOUNT_RANGE_FIXED:
        termination_reason_str = "Завершено штатно (достигнут конец диапазона)"
        return next_account_number

    log_event(
        f"Переходим к следующему аккаунту после fail-soft cleanup: "
        f"{EVE_ACCOUNT_USERNAME_PREFIX}{next_account_number}.",
        important=True,
    )
    time.sleep(PAUSE_BETWEEN_ACCOUNTS_PROCESSING)
    if not start_initial_launcher():
        script_should_terminate = True
        termination_reason_str = "Крит. ошибка: не удалось запустить лаунчер после fail-soft cleanup."
        last_account_for_termination = next_account_number
        return None

    return next_account_number


def run_resume_step_from_current_game(resume_step):
    resume_username = os.environ.get("EVE_RESUME_USERNAME", "manual-resume")
    normalized_step = resume_step.strip().lower().replace("-", "_")
    game_process_baseline = set()

    log_event(f"--- Resume mode: {normalized_step}, username={resume_username} ---", important=True)
    log_event("Resume mode: текущий game process не считается baseline; он должен закрыться при quit-проверке.")

    if normalized_step in {"current_game_full_flow", "full_current_game", "omega_to_quit"}:
        return process_logged_in_game_session(resume_username, game_process_baseline)

    if normalized_step in {"remove_launcher_account", "launcher_remove_account", "remove_account_from_launcher"}:
        if remove_account_from_launcher(resume_username):
            return True
        return retry_account_removal_after_launcher_restart(
            resume_username,
            "Resume: launcher account removal was not confirmed",
        )

    if normalized_step in {"skill_queue", "skills", "skill_queue_only"}:
        return import_omega_skill_queue()

    if normalized_step in {"skill_queue_and_continue", "skill_queue_to_contract", "skills_to_contract"}:
        if not import_omega_skill_queue():
            return False
        if not perform_contract_and_extractor_flow(resume_username):
            return False
        if not perform_final_large_skill_injector_contract_flow():
            return False
        return quit_game_to_launcher(game_process_baseline, allow_force_kill=True)

    if normalized_step in {"contract_extractor", "contracts"}:
        if not perform_contract_and_extractor_flow(resume_username):
            return False
        return quit_game_to_launcher(game_process_baseline)

    if normalized_step in {"active_extractor_first", "extractor_first", "current_extractor_first"}:
        if not perform_active_skill_extractor_flow(
            [
                (GAME_SKILL_ELECTRONIC_UPGRADES_IMG, "Electronic Upgrades"),
                (GAME_SKILL_CPU_MANAGEMENT_IMG, "CPU Management"),
            ],
            "первый extractor resume",
        ):
            return False
        log_event("Resume: после первого extractor повторно не открываем Inventory/Jita; используем уже открытое окно assets.")
        if not activate_skill_extractor_and_extract(
            [
                (GAME_SKILL_WEAPON_UPGRADES_IMG, "Weapon Upgrades"),
                (GAME_SKILL_CPU_MANAGEMENT_IMG, "CPU Management"),
            ],
            "второй extractor resume",
        ):
            return False
        if not perform_final_large_skill_injector_contract_flow():
            return False
        return quit_game_to_launcher(game_process_baseline, allow_force_kill=True)

    if normalized_step in {"final_large_injector_contract", "final_contract", "large_injector_contract"}:
        if not perform_final_large_skill_injector_contract_flow():
            return False
        return quit_game_to_launcher(game_process_baseline, allow_force_kill=True)

    if normalized_step in {
        "final_contract_exact_phrase",
        "exact_phrase_to_finish",
        "large_injector_exact_phrase",
    }:
        if not finish_large_skill_injector_contract_from_exact_phrase_stage():
            return False
        return quit_game_to_launcher(game_process_baseline, allow_force_kill=True)

    log_event(f"ОШИБКА: неизвестный EVE_RESUME_STEP='{resume_step}'.", important=True)
    return False


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
        if START_ACTION_DELAY_SECONDS > 0:
            log_event(
                f"Стартовая пауза {START_ACTION_DELAY_SECONDS:.1f} сек перед действиями. "
                "Можно переключить фокус обратно в игру/лаунчер.",
                important=True,
            )
            time.sleep(START_ACTION_DELAY_SECONDS)
        require_runtime_secrets()

        resume_step = os.environ.get("EVE_RESUME_STEP", "").strip()
        if resume_step:
            resume_success = run_resume_step_from_current_game(resume_step)
            if resume_success:
                termination_reason_str = f"Resume step '{resume_step}' завершён успешно."
            else:
                script_should_terminate = True
                termination_reason_str = f"Resume step '{resume_step}' завершился ошибкой."
            raise SystemExit(0 if resume_success else 1)

        try:
            start_account_number, END_ACCOUNT_RANGE_FIXED = read_account_range_from_env()
        except ValueError as env_range_error:
            script_should_terminate = True
            termination_reason_str = f"Неверный диапазон аккаунтов в env: {env_range_error}"
            raise SystemExit(termination_reason_str)
        except Exception as e_prompt:
            script_should_terminate = True
            termination_reason_str = f"Ошибка при чтении диапазона аккаунтов из env: {e_prompt}"
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
                        next_account = advance_to_next_account_after_failure(
                            current_account_number,
                            current_username,
                            "Launcher: restart failed after Add Account not found",
                        )
                        if next_account is None: break
                        current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                else:
                    next_account = advance_to_next_account_after_failure(
                        current_account_number,
                        current_username,
                        "Launcher: Add Account not found after launcher restart retries",
                    )
                    if next_account is None: break
                    current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
            if not wait_for_login_dialog_ready(timeout_seconds=TIMEOUT_LOGIN_DIALOG_READY):
                log_event(f"ОШИБКА ЛАУНЧЕРА: диалог входа не подтвердился для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher():
                        launcher_restart_attempts_for_current_acc += 1
                        continue
                    else:
                        next_account = advance_to_next_account_after_failure(
                            current_account_number,
                            current_username,
                            "Launcher: restart failed after login dialog not confirmed",
                        )
                        if next_account is None: break
                        current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                else:
                    failed_accounts_details.append((current_account_number, "Launcher: login dialog not confirmed after retries")); account_processing_step_failed = True
            if account_processing_step_failed:
                reason = latest_failure_reason_for_account(current_account_number, "Launcher: account step failed")
                next_account = advance_to_next_account_after_failure(current_account_number, current_username, reason, append_detail=False)
                if next_account is None: break
                current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue

            log_event(f"Шаг 2: Ввод логина и пароля для {current_username}.")
            if not type_text_into_image_field([LAUNCHER_USERNAME_FIELD_IMG, LAUNCHER_USERNAME_LABEL_IMG], "Поле Username", current_username, timeout_seconds=TIMEOUT_LOCATE_SIGN_IN_BTN):
                log_event(f"ОШИБКА ЛАУНЧЕРА: поле Username не найдено для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else:
                        next_account = advance_to_next_account_after_failure(
                            current_account_number,
                            current_username,
                            "Launcher: restart failed after Username field not found",
                        )
                        if next_account is None: break
                        current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                else:
                    failed_accounts_details.append((current_account_number, "Launcher: Username field not found after retries")); account_processing_step_failed = True
            if account_processing_step_failed:
                reason = latest_failure_reason_for_account(current_account_number, "Launcher: account step failed")
                next_account = advance_to_next_account_after_failure(current_account_number, current_username, reason, append_detail=False)
                if next_account is None: break
                current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
            time.sleep(PAUSE_AFTER_USERNAME_TYPE)

            if not type_text_into_image_field([LAUNCHER_PASSWORD_FIELD_IMG, LAUNCHER_PASSWORD_LABEL_IMG], "Поле Password", EVE_ACCOUNT_PASSWORD, timeout_seconds=TIMEOUT_LOCATE_SIGN_IN_BTN):
                log_event(f"ОШИБКА ЛАУНЧЕРА: поле Password не найдено для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else:
                        next_account = advance_to_next_account_after_failure(
                            current_account_number,
                            current_username,
                            "Launcher: restart failed after Password field not found",
                        )
                        if next_account is None: break
                        current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                else:
                    failed_accounts_details.append((current_account_number, "Launcher: Password field not found after retries")); account_processing_step_failed = True
            if account_processing_step_failed:
                reason = latest_failure_reason_for_account(current_account_number, "Launcher: account step failed")
                next_account = advance_to_next_account_after_failure(current_account_number, current_username, reason, append_detail=False)
                if next_account is None: break
                current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
            time.sleep(PAUSE_AFTER_PASSWORD_TYPE)

            if not click_on_image(LAUNCHER_SIGN_IN_BUTTON_IMG, "Кнопка 'Sign In'", timeout_seconds=TIMEOUT_LOCATE_SIGN_IN_BTN):
                log_event(f"ОШИБКА ЛАУНЧЕРА: Кнопка 'Sign In' не найдена для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else:
                        next_account = advance_to_next_account_after_failure(
                            current_account_number,
                            current_username,
                            "Launcher: restart failed after Sign In not found",
                        )
                        if next_account is None: break
                        current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                else: 
                    log_event(f"Пропускаем аккаунт {current_username} из-за ошибки 'Sign In'."); failed_accounts_details.append((current_account_number, "Launcher: 'Sign In' not found after retries")); account_processing_step_failed = True
            if account_processing_step_failed:
                reason = latest_failure_reason_for_account(current_account_number, "Launcher: account step failed")
                next_account = advance_to_next_account_after_failure(current_account_number, current_username, reason, append_detail=False)
                if next_account is None: break
                current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
            if script_should_terminate: break # Проверка после потенциального fail fast

            email_verification_requested_at = time.time()
            post_sign_in_state = wait_for_post_sign_in_state(timeout_seconds=TIMEOUT_AFTER_SIGN_IN_READY)
            if post_sign_in_state == "email_verification":
                if not complete_email_verification(current_username, email_verification_requested_at):
                    log_event(f"ОШИБКА ЛАУНЧЕРА: email verification не пройден для {current_username}.", important=True)
                    failed_accounts_details.append((current_account_number, "Launcher: email verification failed; Gmail/code unavailable"))
                    next_account = advance_to_next_account_after_failure(
                        current_account_number,
                        current_username,
                        "Launcher: email verification failed; Gmail/code unavailable",
                        append_detail=False,
                    )
                    if next_account is None: break
                    current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                if account_processing_step_failed:
                    reason = latest_failure_reason_for_account(current_account_number, "Launcher: account step failed")
                    next_account = advance_to_next_account_after_failure(current_account_number, current_username, reason, append_detail=False)
                    if next_account is None: break
                    current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                if not wait_for_play_ready(timeout_seconds=TIMEOUT_AFTER_SIGN_IN_READY):
                    log_event(f"ОШИБКА ЛАУНЧЕРА: кнопка Play не подтвердилась после email verification для {current_username}.", important=True)
                    failed_accounts_details.append((current_account_number, "Launcher: Play not confirmed after email verification"))
                    next_account = advance_to_next_account_after_failure(
                        current_account_number,
                        current_username,
                        "Launcher: Play not confirmed after email verification",
                        append_detail=False,
                    )
                    if next_account is None: break
                    current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
            elif post_sign_in_state != "play":
                log_event(f"ОШИБКА ЛАУНЧЕРА: после входа не подтвердились ни Play, ни email verification для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher():
                        launcher_restart_attempts_for_current_acc += 1
                        continue
                    else:
                        next_account = advance_to_next_account_after_failure(
                            current_account_number,
                            current_username,
                            "Launcher: restart failed after post-sign-in state not confirmed",
                        )
                        if next_account is None: break
                        current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                else:
                    failed_accounts_details.append((current_account_number, "Launcher: post-sign-in state not confirmed after retries")); account_processing_step_failed = True
            if account_processing_step_failed:
                reason = latest_failure_reason_for_account(current_account_number, "Launcher: account step failed")
                next_account = advance_to_next_account_after_failure(current_account_number, current_username, reason, append_detail=False)
                if next_account is None: break
                current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue

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
                    reset_window_blur_disable_state_for_new_game(current_username)
                    if disable_window_blur_after_game_start() and disable_3d_rendering_after_game_start():
                        game_launched_successfully = True
                    else:
                        failed_accounts_details.append((current_account_number, "In-game: UI blur/3D rendering preparation was not confirmed"))
                        account_processing_step_failed = True
                        quit_game_to_launcher(game_process_baseline)
                else:
                    log_event(f"ОШИБКА: игра не стала готова к вводу для {current_username}.", important=True)
                    if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                        if restart_eve_launcher():
                            launcher_restart_attempts_for_current_acc += 1
                            continue
                        else:
                            next_account = advance_to_next_account_after_failure(
                                current_account_number,
                                current_username,
                                "Launcher: restart failed after game readiness not confirmed",
                            )
                            if next_account is None: break
                            current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                    else:
                        failed_accounts_details.append((current_account_number, "In-game: readiness not confirmed after launch")); account_processing_step_failed = True
            else:
                log_event(f"ОШИБКА ЛАУНЧЕРА: Play не привёл к статусу Client is running для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else:
                        next_account = advance_to_next_account_after_failure(
                            current_account_number,
                            current_username,
                            "Launcher: restart failed after Play did not start client",
                        )
                        if next_account is None: break
                        current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
                else:
                    log_event(f"Пропускаем аккаунт {current_username} из-за ошибки 'Play'."); failed_accounts_details.append((current_account_number, "Launcher: Play did not lead to Client is running")); account_processing_step_failed = True
            if account_processing_step_failed:
                reason = latest_failure_reason_for_account(current_account_number, "Launcher/game launch step failed")
                next_account = advance_to_next_account_after_failure(current_account_number, current_username, reason, append_detail=False)
                if next_account is None: break
                current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
            if script_should_terminate: break # Проверка после потенциального fail fast
            
            if game_launched_successfully:
                log_event(f"Шаг 4: Закрытие popup/event окон и выход из игры для {current_username}.")
                launcher_restart_attempts_for_current_acc = 0 
                if process_logged_in_game_session(current_username, game_process_baseline):
                    log_event(f"--- УСПЕХ: Игровая сессия для {current_username} закрыта. ---", important=True)

                    log_event(f"Шаг 5: Удаление аккаунта {current_username} из лаунчера.")
                    time.sleep(PAUSE_BEFORE_ACCOUNT_DELETION_ACTIONS)
                    if not remove_account_from_launcher(current_username):
                        log_event(f"Удаление аккаунта {current_username} из лаунчера не выполнено в image-only режиме.", important=True)
                        account_removal_reason = "Launcher: account removal was not confirmed by image templates"
                        if not retry_account_removal_after_launcher_restart(current_username, account_removal_reason):
                            failed_accounts_details.append((current_account_number, account_removal_reason))
                            next_account = advance_to_next_account_after_failure(
                                current_account_number,
                                current_username,
                                account_removal_reason,
                                append_detail=False,
                            )
                            if next_account is None: break
                            current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue

                    capsulers_successfully_processed += 1
                    successfully_processed_usernames.append(current_username)
                    consecutive_registration_failures = 0
                    log_event(f"--- УСПЕХ ПОЛНЫЙ: Аккаунт {current_username} полностью обработан. ---", important=True)
                else:
                    log_event(f"--- НЕУДАЧА: обязательный in-game flow для {current_username} не завершён или выход не подтверждён. ---", important=True)
                    failed_accounts_details.append((current_account_number, "In-game: required account flow or Quit Game failed"))
                    next_account = advance_to_next_account_after_failure(
                        current_account_number,
                        current_username,
                        "In-game: required account flow or Quit Game failed",
                        append_detail=False,
                    )
                    if next_account is None: break
                    current_account_number = next_account; launcher_restart_attempts_for_current_acc = 0; continue
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
        if script_should_terminate:
            log_event(f"Критическая ошибка/остановка (SystemExit): {e}", important=True)
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
