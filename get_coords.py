import pyautogui
import time

print("Перемести мышь на нужную позицию в течение следующих 5 секунд...")
time.sleep(5)
try:
    while True:
        x, y = pyautogui.position()
        position_str = f"X: {str(x).rjust(4)} Y: {str(y).rjust(4)}"
        print(position_str, end='')
        print('\b' * len(position_str), end='', flush=True) # Обновление строки на месте
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\nОпределение координат завершено.")