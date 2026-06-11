import argparse
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image

from eve_config import (
    MATCH_TEMPLATE_ASSETS,
    apply_linux_xauthority_fallback,
    install_wayland_screenshot_backend,
    resource_path,
)


def parse_region(value):
    try:
        x_value, y_value, width, height = [int(part.strip()) for part in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("region must be x,y,width,height") from exc
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("region width and height must be positive")
    return x_value, y_value, width, height


def capture_screen():
    apply_linux_xauthority_fallback()
    import pyautogui

    install_wayland_screenshot_backend(pyautogui)
    return pyautogui.screenshot().convert("RGBA")


def backup_existing(path, backup_dir):
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def main():
    parser = argparse.ArgumentParser(description="Capture or crop a replacement EVE image template.")
    parser.add_argument("template", help="Template filename, for example add_account_button.png")
    parser.add_argument("--region", required=True, type=parse_region, help="Crop region as x,y,width,height")
    parser.add_argument("--source", type=Path, help="Existing screenshot. If omitted, captures current screen.")
    parser.add_argument("--backup-dir", type=Path, default=Path("template_backups"))
    parser.add_argument("--allow-new", action="store_true", help="Allow template names that are not in MATCH_TEMPLATE_ASSETS.")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    template_name = Path(args.template).name
    if template_name not in MATCH_TEMPLATE_ASSETS and not args.allow_new:
        print(f"Unknown runtime template: {template_name}")
        print("Known templates:")
        for known_template in MATCH_TEMPLATE_ASSETS:
            print(f"  {known_template}")
        raise SystemExit(2)

    source_image = Image.open(args.source).convert("RGBA") if args.source else capture_screen()
    x_value, y_value, width, height = args.region
    crop_box = (x_value, y_value, x_value + width, y_value + height)
    if crop_box[2] > source_image.width or crop_box[3] > source_image.height:
        raise SystemExit(f"Region {args.region} exceeds source image size {source_image.width}x{source_image.height}.")

    output_path = resource_path(template_name)
    backup_path = None if args.no_backup else backup_existing(output_path, resource_path(args.backup_dir))
    source_image.crop(crop_box).save(output_path)

    if backup_path:
        print(f"Backup: {backup_path}")
    print(f"Updated: {output_path} ({width}x{height})")


if __name__ == "__main__":
    main()
