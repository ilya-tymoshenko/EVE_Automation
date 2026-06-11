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

from eve_config import describe_launcher_command, get_launcher_command, resource_path

# --- Пользовательские настройки ---
SKILLS_FILE_PATH = "skills.txt"
LOG_FILE_PATH = "script_run_log.txt" # Логи будут писаться сюда непрерывно
FAILURE_CONTEXT_DIR = "runtime_failures"

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
PAUSE_FOR_GAME_TO_CLOSE = 5.0
PAUSE_FOR_GAME_TO_CLOSE_EMERGENCY = 5.0
PAUSE_BEFORE_ACCOUNT_DELETION_ACTIONS = 2.0
PAUSE_AFTER_ACCOUNT_SETTINGS_CLICK = 1
PAUSE_AFTER_REMOVE_ACCOUNT_CLICK = 1
PAUSE_AFTER_CONFIRM_REMOVE_CLICK = 1
PAUSE_BETWEEN_ACCOUNTS_PROCESSING = 2

TIMEOUT_LOCATE_CALDARI_FACTION = 20
TIMEOUT_LOCATE_NAME_BUTTON = 15
TIMEOUT_LOCATE_ADD_ACCOUNT_BTN = 25
TIMEOUT_LOCATE_ADD_ACCOUNT_BTN_AFTER_UNBUG = 20
TIMEOUT_LOCATE_SIGN_IN_BTN = 20
TIMEOUT_LOCATE_PLAY_BTN = 30

# --- Настройки для ЛАУНЧЕРА ---
LAUNCHER_ADD_ACCOUNT_BUTTON_IMG = 'add_account_button.png'
LAUNCHER_USERNAME_X, LAUNCHER_USERNAME_Y = 1100, 300
LAUNCHER_PASSWORD_X, LAUNCHER_PASSWORD_Y = 1100, 377
LAUNCHER_SIGN_IN_BUTTON_IMG = 'sign_in_button.png'
LAUNCHER_PLAY_BUTTON_IMG = 'launcher_play_button.png'
LAUNCHER_ACCOUNT_SETTINGS_X, LAUNCHER_ACCOUNT_SETTINGS_Y = 1238, 136
LAUNCHER_REMOVE_ACCOUNT_X, LAUNCHER_REMOVE_ACCOUNT_Y = 930, 489
LAUNCHER_CONFIRM_REMOVE_X, LAUNCHER_CONFIRM_REMOVE_Y = 1316, 472

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

# --- Остальные функции (common_launcher_start_logic, perform_character_creation_and_setup и т.д.) остаются БЕЗ ИЗМЕНЕНИЙ в своей логике ---
# Они будут использовать обновленный log_event, который пишет в файл сразу.

def common_launcher_start_logic(is_initial_start=False):
    global launcher_restarts_count
    action = "Первоначальный запуск" if is_initial_start else "Перезапуск"
    launcher_command = get_launcher_command()
    log_event(f"{action} лаунчера EVE Online командой: {describe_launcher_command()}", important=True)
    try:
        subprocess.Popen(launcher_command)
        log_event("Команда на запуск лаунчера отправлена.")
        wait_time = PAUSE_INITIAL_LAUNCHER_LOAD if is_initial_start else PAUSE_RESTART_LAUNCHER_LOAD
        log_event(f"Ожидание загрузки лаунчера ({wait_time} секунд)...")
        time.sleep(wait_time)
        log_event("Попытка переключить лаунчер в полноэкранный режим (F11)...")
        time.sleep(PAUSE_BEFORE_F11_ATTEMPT)
        pyautogui.press('f11')
        time.sleep(PAUSE_AFTER_F11_ATTEMPT)
        log_event("Предполагается, что лаунчер в полноэкранном режиме.")
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
    return common_launcher_start_logic(is_initial_start=True)

def restart_eve_launcher():
    return common_launcher_start_logic(is_initial_start=False)

def try_unbug_launcher_clicks():
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


def click_on_image(image_filename, description, confidence_level=0.8, timeout_seconds=10):
    log_event(f"Ищем '{description}' (файл: {image_filename}, таймаут: {timeout_seconds} сек)...")
    image_path = str(resource_path(image_filename))
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence_level)
            if location:
                human_click(location.x, location.y)
                log_event(f"Клик по '{description}' выполнен.")
                return True
            else:
                time.sleep(PAUSE_SHORT)
        except Exception as e:
            log_event(f"ИСКЛЮЧЕНИЕ при поиске/клике '{description}': {e}")
            if "confidence" in str(e).lower() and "opencv" in str(e).lower():
                log_event(">>> ВНИМАНИЕ: Для 'confidence' нужен OpenCV. Установи: pip install opencv-python")
    log_event(f"ОШИБКА: '{description}' ({image_filename}) не найдено на экране.", important=True)
    return False

def find_image(image_filename, description, confidence_level=0.8, timeout_seconds=10):
    log_event(f"Проверяем наличие '{description}' (файл: {image_filename}, таймаут: {timeout_seconds} сек)...")
    image_path = str(resource_path(image_filename))
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            if pyautogui.locateOnScreen(image_path, confidence=confidence_level):
                log_event(f"'{description}' найдено на экране.")
                return True
            else:
                time.sleep(PAUSE_SHORT)
        except Exception as e:
            log_event(f"ИСКЛЮЧЕНИЕ при поиске '{description}': {e}")
            if "confidence" in str(e).lower() and "opencv" in str(e).lower():
                log_event(">>> ВНИМАНИЕ: Для 'confidence' нужен OpenCV. Установи: pip install opencv-python")
            return False
    log_event(f"ОШИБКА ПРОВЕРКИ: '{description}' ({image_filename}) не найдено на экране.", important=True)
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
                    human_click(location.x, location.y)
                    log_event(f"Клик по '{description}' (используя '{image_filename}') выполнен.")
                    return True
            except Exception as e:
                log_event(f"ИСКЛЮЧЕНИЕ при поиске '{image_filename}' для '{description}': {e}")
        time.sleep(attempt_interval)
    log_event(f"ОШИБКА: Ни один из вариантов для '{description}' не найден.", important=True)
    return False

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

def perform_character_creation_and_setup(chabiad_name_number, skills_data_for_plan):
    global script_should_terminate, termination_reason_str, last_account_for_termination
    log_event(f"--- Начало создания персонажа Chabiad {chabiad_name_number} ---", important=True)
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
            log_file_writer.write(f"Всего успешно создано и настроено капсулёров: {capsulers_successfully_processed} (из них имен в списке: {len(successfully_processed_usernames)})\n")
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
                log_file_writer.write("Проблемных аккаунтов (с точки зрения регистрации или критических ошибок лаунчера) не зафиксировано.\n")
            
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
        all_skills_data = read_skills_from_file(SKILLS_FILE_PATH)
        if not all_skills_data:
            script_should_terminate = True
            termination_reason_str = "Не удалось загрузить навыки из файла."
            raise SystemExit(termination_reason_str) 

        try:
            start_account_number_str = os.environ.get("EVE_START_ACCOUNT")
            if start_account_number_str:
                log_event(f"Начальный номер взят из EVE_START_ACCOUNT={start_account_number_str}.")
            else:
                start_account_number_str = pyautogui.prompt(
                    text='Введите НАЧАЛЬНЫЙ номер для аккаунта EVE и имени Chabiad (например, 1):',
                    title='Начальный номер', default='1'
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

        log_event(f"Начальная пауза после запуска лаунчера ({PAUSE_AFTER_LAUNCHER_FIRST_START} секунд)...")
        time.sleep(PAUSE_AFTER_LAUNCHER_FIRST_START)
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
            time.sleep(PAUSE_AFTER_ADD_ACCOUNT_CLICK)

            log_event(f"Шаг 2: Ввод логина и пароля для {current_username}.")
            human_click(LAUNCHER_USERNAME_X, LAUNCHER_USERNAME_Y); log_event(f"Клик по полю Username."); time.sleep(PAUSE_SHORT)
            pyautogui.typewrite(current_username, interval=0.15); log_event(f"Username '{current_username}' введен."); time.sleep(PAUSE_AFTER_USERNAME_TYPE)
            human_click(LAUNCHER_PASSWORD_X, LAUNCHER_PASSWORD_Y); log_event(f"Клик по полю Password."); time.sleep(PAUSE_SHORT)
            pyautogui.typewrite(EVE_ACCOUNT_PASSWORD, interval=0.15); log_event(f"Пароль введен."); time.sleep(PAUSE_AFTER_PASSWORD_TYPE)

            if not click_on_image(LAUNCHER_SIGN_IN_BUTTON_IMG, "Кнопка 'Sign In'", timeout_seconds=TIMEOUT_LOCATE_SIGN_IN_BTN):
                log_event(f"ОШИБКА ЛАУНЧЕРА: Кнопка 'Sign In' не найдена для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else: script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после 'Sign In' fail."; last_account_for_termination = current_account_number; break
                else: 
                    log_event(f"Пропускаем аккаунт {current_username} из-за ошибки 'Sign In'."); failed_accounts_details.append((current_account_number, "Launcher: 'Sign In' not found after retries")); account_processing_step_failed = True
            if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue 
            if script_should_terminate: break # Проверка после потенциального fail fast

            time.sleep(PAUSE_AFTER_SIGN_IN_CLICK) 

            log_event(f"Шаг 3: Запуск игры для {current_username}.")
            if click_on_image(LAUNCHER_PLAY_BUTTON_IMG, "Кнопка 'Играть'", confidence_level=0.75, timeout_seconds=TIMEOUT_LOCATE_PLAY_BTN):
                log_event(f"Кнопка 'Играть' нажата. Ожидание запуска игры ({PAUSE_AFTER_PLAY_CLICK_FOR_GAME_LOAD} секунд)...")
                time.sleep(PAUSE_AFTER_PLAY_CLICK_FOR_GAME_LOAD)
                game_launched_successfully = True
            else:
                log_event(f"ОШИБКА ЛАУНЧЕРА: Кнопка 'Играть' не найдена для {current_username}.", important=True)
                if launcher_restart_attempts_for_current_acc < MAX_LAUNCHER_RESTART_ATTEMPTS:
                    if restart_eve_launcher(): launcher_restart_attempts_for_current_acc += 1; time.sleep(PAUSE_AFTER_LAUNCHER_RESTART_FOR_ACC); continue
                    else: script_should_terminate = True; termination_reason_str = "Крит. ошибка: Перезапуск лаунчера после 'Play' fail."; last_account_for_termination = current_account_number; break
                else:
                    log_event(f"Пропускаем аккаунт {current_username} из-за ошибки 'Play'."); failed_accounts_details.append((current_account_number, "Launcher: 'Play' not found after retries")); account_processing_step_failed = True
            if account_processing_step_failed : current_account_number +=1; launcher_restart_attempts_for_current_acc = 0; continue
            if script_should_terminate: break # Проверка после потенциального fail fast
            
            if game_launched_successfully:
                log_event(f"Шаг 4: Создание персонажа и настройка навыков для {current_username}.")
                launcher_restart_attempts_for_current_acc = 0 
                if perform_character_creation_and_setup(current_account_number, all_skills_data):
                    log_event(f"--- УСПЕХ: Внутриигровые операции для Chabiad {current_account_number} ({current_username}) завершены. ---", important=True)
                    capsulers_successfully_processed += 1
                    successfully_processed_usernames.append(current_username)
                    consecutive_registration_failures = 0
                else:
                    log_event(f"--- НЕУДАЧА: Внутриигровые операции для Chabiad {current_account_number} ({current_username}) не удались. ---", important=True)
                    failed_accounts_details.append((current_account_number, "In-game: Character creation/setup/verification failed"))
                    total_registration_failures += 1
                    consecutive_registration_failures += 1
                    account_processing_step_failed = True 

                    if consecutive_registration_failures >= 2:
                        script_should_terminate = True; termination_reason_str = "2 последовательных неудачных регистрации персонажа."; last_account_for_termination = current_account_number; break
                    if total_registration_failures >= 5:
                        script_should_terminate = True; termination_reason_str = "5 общих неудачных регистраций персонажа."; last_account_for_termination = current_account_number; break
                
                log_event(f"Шаг 5: Удаление аккаунта {current_username} из лаунчера.")
                time.sleep(PAUSE_BEFORE_ACCOUNT_DELETION_ACTIONS)
                human_click(LAUNCHER_ACCOUNT_SETTINGS_X, LAUNCHER_ACCOUNT_SETTINGS_Y); log_event("Клик по 'Настройки учётной записи'."); time.sleep(PAUSE_AFTER_ACCOUNT_SETTINGS_CLICK)
                human_click(LAUNCHER_REMOVE_ACCOUNT_X, LAUNCHER_REMOVE_ACCOUNT_Y); log_event("Клик по 'Удалить учётную запись'."); time.sleep(PAUSE_AFTER_REMOVE_ACCOUNT_CLICK)
                human_click(LAUNCHER_CONFIRM_REMOVE_X, LAUNCHER_CONFIRM_REMOVE_Y); log_event("Клик по 'Подтвердить удаление'."); time.sleep(PAUSE_AFTER_CONFIRM_REMOVE_CLICK)
                log_event(f"Аккаунт {current_username} удален из лаунчера.")
                if not account_processing_step_failed: 
                     log_event(f"--- УСПЕХ ПОЛНЫЙ: Аккаунт {current_username} полностью обработан. ---", important=True)
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
