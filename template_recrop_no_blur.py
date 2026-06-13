import argparse
import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from eve_config import (
    MATCH_TEMPLATE_ASSETS,
    apply_linux_xauthority_fallback,
    install_wayland_screenshot_backend,
    resource_path,
)


DEFAULT_EXCLUDE = {
    "screens/game_ui_setting.png",
    "screens/game_enable_window_blur.png",
}


def game_templates():
    return [
        template
        for template in MATCH_TEMPLATE_ASSETS
        if template.startswith("screens/game_") and template not in DEFAULT_EXCLUDE
    ]


def parse_template_list(value):
    if not value:
        return game_templates()
    return [item.strip() for item in value.split(",") if item.strip()]


def image_to_cv(image):
    return np.array(image.convert("RGB"))


def capture_screen(output_path=None):
    apply_linux_xauthority_fallback()
    import pyautogui

    install_wayland_screenshot_backend(pyautogui)
    screenshot = pyautogui.screenshot().convert("RGB")
    if output_path:
        screenshot.save(output_path)
    return screenshot


def locate_template(screen_image, template_name, threshold):
    template_path = resource_path(template_name)
    if not template_path.exists():
        return {
            "template": template_name,
            "status": "missing",
            "score": None,
            "bbox": None,
            "size": None,
        }

    template_image = Image.open(template_path).convert("RGB")
    screen_cv = image_to_cv(screen_image)
    template_cv = image_to_cv(template_image)
    screen_height, screen_width = screen_cv.shape[:2]
    template_width, template_height = template_image.size

    if template_width > screen_width or template_height > screen_height:
        return {
            "template": template_name,
            "status": "too_large",
            "score": None,
            "bbox": None,
            "size": [template_width, template_height],
        }

    result = cv2.matchTemplate(screen_cv, template_cv, cv2.TM_CCOEFF_NORMED)
    _, max_value, _, max_location = cv2.minMaxLoc(result)
    x_value, y_value = max_location
    status = "match" if max_value >= threshold else "low_score"
    return {
        "template": template_name,
        "status": status,
        "score": round(float(max_value), 4),
        "bbox": [int(x_value), int(y_value), int(template_width), int(template_height)],
        "size": [template_width, template_height],
    }


def locate_center_on_screen(template_name, threshold, timeout_seconds, description):
    apply_linux_xauthority_fallback()
    import pyautogui

    install_wayland_screenshot_backend(pyautogui)
    template_path = str(resource_path(template_name))
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            location = pyautogui.locateCenterOnScreen(template_path, confidence=threshold)
            if location:
                print(f"found {description}: {template_name} at ({location.x}, {location.y})")
                return location
        except Exception as exc:
            error_text = str(exc).strip()
            if error_text and error_text != last_error:
                print(f"search error for {description}: {error_text}")
                last_error = error_text
        time.sleep(0.5)
    return None


def click_template(template_name, description, threshold=0.75, timeout_seconds=15):
    import pyautogui

    location = locate_center_on_screen(template_name, threshold, timeout_seconds, description)
    if not location:
        return False
    pyautogui.moveTo(location.x, location.y, duration=0.12)
    pyautogui.click(location.x, location.y)
    time.sleep(0.8)
    return True


def toggle_window_blur(threshold=0.75):
    apply_linux_xauthority_fallback()
    import pyautogui

    install_wayland_screenshot_backend(pyautogui)
    print("opening Esc menu")
    pyautogui.press("esc")
    time.sleep(1.0)
    if not click_template("screens/game_ui_setting.png", "User Interface settings", threshold=threshold):
        return False
    if not click_template("screens/game_enable_window_blur.png", "Enable window blur", threshold=threshold):
        return False
    time.sleep(0.8)
    pyautogui.press("esc")
    time.sleep(1.5)
    return True


def crop_with_margin(image, bbox, margin):
    x_value, y_value, width, height = bbox
    left = max(0, x_value - margin)
    top = max(0, y_value - margin)
    right = min(image.width, x_value + width + margin)
    bottom = min(image.height, y_value + height + margin)
    return image.crop((left, top, right, bottom))


def backup_existing(path, backup_dir):
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def save_candidate(after_image, output_dir, row, margin):
    if row["status"] != "match" or not row["bbox"]:
        return None
    output_path = output_dir / row["template"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    crop = crop_with_margin(after_image, row["bbox"], margin)
    crop.save(output_path)
    return output_path


def load_font(size=14):
    for font_path in (
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        path = Path(font_path)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def create_contact_sheet(rows, output_dir, sheet_path, max_thumb_width=280, row_height=96):
    matched_rows = [row for row in rows if row.get("candidate_path")]
    if not matched_rows:
        return None

    font = load_font(13)
    width = 760
    height = 34 + len(matched_rows) * row_height
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), "template | old | no-blur candidate", fill="black", font=font)

    y_value = 32
    for row in matched_rows:
        template_path = resource_path(row["template"])
        candidate_path = Path(row["candidate_path"])
        old_image = Image.open(template_path).convert("RGB")
        new_image = Image.open(candidate_path).convert("RGB")

        def thumbnail(image):
            copy = image.copy()
            copy.thumbnail((max_thumb_width, row_height - 18))
            return copy

        old_thumb = thumbnail(old_image)
        new_thumb = thumbnail(new_image)
        label = f"{row['template']} score={row['score']}"
        draw.text((8, y_value + 4), label[:42], fill="black", font=font)
        sheet.paste(old_thumb, (330, y_value + 4))
        sheet.paste(new_thumb, (530, y_value + 4))
        y_value += row_height

    sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(sheet_path)
    return sheet_path


def replace_templates(rows, output_dir, backup_dir):
    replaced = []
    for row in rows:
        candidate_path = row.get("candidate_path")
        if not candidate_path:
            continue
        target_path = resource_path(row["template"])
        backup_path = backup_existing(target_path, backup_dir)
        shutil.copy2(candidate_path, target_path)
        replaced.append({
            "template": row["template"],
            "target": str(target_path),
            "backup": str(backup_path) if backup_path else None,
        })
    return replaced


def main():
    parser = argparse.ArgumentParser(
        description="Recrop EVE templates from the same screen bboxes after disabling window blur."
    )
    parser.add_argument("--templates", help="Comma-separated template paths. Default: all in-game screens/game_*.png templates.")
    parser.add_argument("--before", type=Path, help="Baseline screenshot before blur toggle. If omitted, captures current screen.")
    parser.add_argument("--after", type=Path, help="Screenshot after blur toggle. If omitted, captures after optional toggle.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--threshold", type=float, default=0.75)
    parser.add_argument("--margin", type=int, default=0)
    parser.add_argument("--no-toggle", action="store_true", help="Do not click Esc/User Interface/Enable window blur.")
    parser.add_argument("--replace", action="store_true", help="Replace runtime templates from candidate crops after creating backups.")
    parser.add_argument("--backup-dir", type=Path, default=Path("template_backups"))
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_dir or Path("template_recrops") / f"no_blur_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    before_path = args.before or output_dir / "before_blur_toggle.png"
    after_path = args.after or output_dir / "after_blur_toggle.png"

    if args.before:
        before_image = Image.open(args.before).convert("RGB")
    else:
        before_image = capture_screen(before_path)

    templates = parse_template_list(args.templates)
    rows = [locate_template(before_image, template, args.threshold) for template in templates]

    matched = [row for row in rows if row["status"] == "match"]
    print(f"matched templates before toggle: {len(matched)}/{len(rows)}")
    for row in rows:
        score = "-" if row["score"] is None else f"{row['score']:.4f}"
        print(f"{row['status']:<10} {score:>7} {row['template']}")

    if args.after:
        after_image = Image.open(args.after).convert("RGB")
    else:
        if not args.no_toggle:
            if not toggle_window_blur(threshold=args.threshold):
                raise SystemExit("Could not toggle window blur through image templates.")
        after_image = capture_screen(after_path)

    for row in rows:
        candidate_path = save_candidate(after_image, output_dir, row, args.margin)
        row["candidate_path"] = str(candidate_path) if candidate_path else None

    sheet_path = output_dir / "contact_sheet.png"
    created_sheet = create_contact_sheet(rows, output_dir, sheet_path)

    replaced = []
    if args.replace:
        replaced = replace_templates(rows, output_dir, args.backup_dir)

    manifest = {
        "before": str(before_path),
        "after": str(after_path),
        "threshold": args.threshold,
        "margin": args.margin,
        "output_dir": str(output_dir),
        "contact_sheet": str(created_sheet) if created_sheet else None,
        "templates": rows,
        "replaced": replaced,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"output_dir: {output_dir}")
    print(f"manifest: {manifest_path}")
    if created_sheet:
        print(f"contact_sheet: {created_sheet}")
    if args.replace:
        print(f"replaced: {len(replaced)}")


if __name__ == "__main__":
    main()
