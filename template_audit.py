import argparse
import json
from pathlib import Path

import cv2
from PIL import Image

from eve_config import (
    MATCH_TEMPLATE_ASSETS,
    apply_linux_xauthority_fallback,
    install_wayland_screenshot_backend,
    resource_path,
)


def capture_screen(output_path=None):
    apply_linux_xauthority_fallback()
    import pyautogui

    install_wayland_screenshot_backend(pyautogui)
    screenshot = pyautogui.screenshot().convert("RGB")
    if output_path:
        screenshot.save(output_path)
    return screenshot


def image_to_cv(image):
    import numpy as np

    return np.array(image.convert("RGB"))


def audit_template(screen_cv, template_name, threshold):
    template_path = resource_path(template_name)
    if not template_path.exists():
        return {
            "template": template_name,
            "status": "missing",
            "score": None,
            "x": None,
            "y": None,
            "width": None,
            "height": None,
        }

    template = Image.open(template_path).convert("RGB")
    template_cv = image_to_cv(template)
    screen_height, screen_width = screen_cv.shape[:2]
    template_width, template_height = template.size

    if template_width > screen_width or template_height > screen_height:
        return {
            "template": template_name,
            "status": "too_large",
            "score": None,
            "x": None,
            "y": None,
            "width": template_width,
            "height": template_height,
        }

    result = cv2.matchTemplate(screen_cv, template_cv, cv2.TM_CCOEFF_NORMED)
    _, max_value, _, max_location = cv2.minMaxLoc(result)
    status = "match" if max_value >= threshold else "low_score"
    return {
        "template": template_name,
        "status": status,
        "score": round(float(max_value), 4),
        "x": int(max_location[0]),
        "y": int(max_location[1]),
        "width": template_width,
        "height": template_height,
    }


def print_table(rows):
    print(f"{'status':<10} {'score':>7} {'x':>5} {'y':>5} {'size':>11} template")
    print("-" * 72)
    for row in rows:
        score = "-" if row["score"] is None else f"{row['score']:.4f}"
        x_value = "-" if row["x"] is None else str(row["x"])
        y_value = "-" if row["y"] is None else str(row["y"])
        size = "-" if row["width"] is None else f"{row['width']}x{row['height']}"
        print(f"{row['status']:<10} {score:>7} {x_value:>5} {y_value:>5} {size:>11} {row['template']}")


def main():
    parser = argparse.ArgumentParser(description="Audit EVE image templates against a screenshot.")
    parser.add_argument("--screenshot", type=Path, help="Existing screenshot to audit. If omitted, captures the current screen.")
    parser.add_argument("--save-screenshot", type=Path, help="Save the captured current screen to this path.")
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a table.")
    parser.add_argument("--fail-below", action="store_true", help="Exit 1 if any template is missing or below threshold.")
    args = parser.parse_args()

    if args.screenshot:
        screenshot = Image.open(args.screenshot).convert("RGB")
    else:
        screenshot = capture_screen(args.save_screenshot)

    screen_cv = image_to_cv(screenshot)
    rows = [audit_template(screen_cv, template_name, args.threshold) for template_name in MATCH_TEMPLATE_ASSETS]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows)

    if args.fail_below and any(row["status"] != "match" for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
