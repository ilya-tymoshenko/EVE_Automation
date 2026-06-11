import pyautogui
import time
# Подставь СВОИ значения из eve_bot.py
SCROLL_AREA_X = 600 # Твой LAUNCHER_SCROLL_AREA_X
SCROLL_AREA_Y = 119 # Твой LAUNCHER_SCROLL_AREA_Y
SCROLL_UNITS1 = 500  # Твой LAUNCHER_SCROLL_UNITS
SCROLL_UNITS2 = 85
print("Убедись, что окно лаунчера активно. Скрипт начнет через 3 секунды.")
time.sleep(3)
pyautogui.moveTo(SCROLL_AREA_X, SCROLL_AREA_Y)
time.sleep(0.2)
pyautogui.scroll(-SCROLL_UNITS1) 
