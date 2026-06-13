import argparse
import io
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, BOTTOM, DISABLED, END, LEFT, NORMAL, RIGHT, TOP, X, Button, Frame, Label, StringVar, Text, Tk, messagebox

from PIL import Image, ImageGrab, ImageTk

from eve_config import resource_path


DEFAULT_OUTPUT_LOG = Path("template_manual_recapture_log.jsonl")
DEFAULT_BACKUP_DIR = Path("template_backups") / "manual_recapture"
MAX_PREVIEW_SIZE = (360, 220)
MAX_PASTE_PREVIEW_SIZE = (360, 220)


SCRIPT_FLOW_TEMPLATE_ORDER = [
    "game_undock_button.png",
    "game_new_event.png",
    "game_new_event_close_button.png",
    "game_alpa_status_downgrade_event.png",
    "game_alpha_status_close_button.png",
    "game_ui_setting.png",
    "game_enable_window_blur.png",
    "game_7_days_omega_offer_in_store_1.png",
    "game_7_days_omega_offer_in_store_2.png",
    "game_7_days_omega_offer_in_store_3(free button).png",
    "game_log_off_button.png",
    "game_log_off_yes_button.png",
    "game_gift_claim_button.png",
    "game_character_pick.png",
    "game_gifts_button.png",
    "game_gifts_select_all_button.png",
    "game_redeem_to_current_station.png",
    "game_redeem_yes_button.png",
    "game_expert_system_event.png",
    "x2.png",
    "game_skills.png",
    "game_skills2.png",
    "game_skills_menu.png",
    "game_skill_queue_replace_button.png",
    "game_success_skill.png",
    "game_close3.png",
    "game_plus_button.png",
    "game_confirm_button.png",
    "game_close1.png",
    "game_close2.png",
    "game_menu_button.png",
    "game_finance_button.png",
    "game_contracts_button.png",
    "game_my_contracts_button.png",
    "game_contract_name_button.png",
    "game_contract_accept_button.png",
    "game_contract_yes_button.png",
    "game_contract_close_button.png",
    "x.png",
    "game_inventory_icon.png",
    "game_jita4.png",
    "game_skill_extractor.png",
    "game_activate_skill_extractor.png",
    "game_leave_current_ship_button.png",
    "game_skills_engineering.png",
    "game_skill_electronic_upgrades.png",
    "game_skill_cpu_management.png",
    "game_skill_weapon_upgrades.png",
    "game_extract_skill_button.png",
    "game_big_extract_button.png",
    "game_claim_button.png",
    "game_large_skill_injector.png",
    "game_create_contract.png",
    "game_private.png",
    "game_name.png",
    "game_search_by.png",
    "game_exact_phrase_main.png",
    "game_exact_phrase.png",
    "game_only_exact_phrase.png",
    "game_next_button.png",
    "game_type_box.png",
    "game_finish_button.png",
    "game_yes_button.png",
    "success_screen.png",
    "game_quit_game_button.png",
    "game_yes_button_after_quit.png",
]


FLOW_HINTS = {
    "game_7_days_omega_offer_in_store_1.png": "Alt+L+4 -> дождаться Store -> карточка 7 days Omega.",
    "game_7_days_omega_offer_in_store_2.png": "Store -> открыть карточку 7 days Omega.",
    "game_7_days_omega_offer_in_store_3(free button).png": "Store -> карточка 7 days Omega -> кнопка Free.",
    "game_log_off_button.png": "Esc menu после claim Omega -> Log Off.",
    "game_log_off_yes_button.png": "Esc menu -> Log Off -> подтверждение Yes.",
    "game_gift_claim_button.png": "После Log Off игра возвращает на экран gift claim.",
    "game_character_pick.png": "После Gift Claim -> Esc -> выбор персонажа.",
    "game_gifts_button.png": "В игре на станции -> Gifts.",
    "game_gifts_select_all_button.png": "Gifts window -> Select All.",
    "game_redeem_to_current_station.png": "Gifts window -> Select All -> Redeem to current station.",
    "game_redeem_yes_button.png": "Redeem to current station -> подтверждение Yes.",
    "game_expert_system_event.png": "Может появиться после Redeem gifts.",
    "x2.png": "Закрытие Expert System/event окна.",
    "game_skills.png": "Левый Neocom -> Skills icon.",
    "game_skills2.png": "Альтернативный вид Skills icon.",
    "game_skills_menu.png": "Окно Skills -> menu button.",
    "game_skill_queue_replace_button.png": "Skills menu -> Replace skill queue with clipboard.",
    "game_success_skill.png": "После Replace skill queue -> успешный импорт/строка skill queue.",
    "game_close3.png": "Закрытие popup успешного импорта, contract confirmation, final claim/success windows.",
    "game_plus_button.png": "Skills queue -> кнопка Plus после импортирования.",
    "game_confirm_button.png": "Skills queue -> после Plus -> Confirm.",
    "game_close1.png": "Skills queue confirmation/window -> Close.",
    "game_close2.png": "Skills queue confirmation/window -> alternative Close.",
    "game_menu_button.png": "В игре на станции -> левый верхний game menu button.",
    "game_finance_button.png": "Game menu -> Finance.",
    "game_contracts_button.png": "Finance/menu -> Contracts.",
    "game_my_contracts_button.png": "Contracts window -> My Contracts.",
    "game_contract_name_button.png": "My Contracts -> строка/имя контракта.",
    "game_contract_accept_button.png": "Contract detail -> Accept.",
    "game_contract_yes_button.png": "Accept contract -> Yes confirmation.",
    "game_contract_close_button.png": "Contract window -> Close.",
    "x.png": "Best-effort close крестик на окне.",
    "game_inventory_icon.png": "Neocom/station UI -> Inventory icon.",
    "game_jita4.png": "Inventory -> Jita 4 item/location.",
    "game_skill_extractor.png": "Inventory -> Skill Extractor item.",
    "game_activate_skill_extractor.png": "Right click Skill Extractor -> Activate.",
    "game_leave_current_ship_button.png": "After Activate Skill Extractor -> prompt to leave current ship / enter capsule.",
    "game_skills_engineering.png": "Extractor/Skills -> Engineering category.",
    "game_skill_electronic_upgrades.png": "Engineering skills -> Electronic Upgrades; right-click -> Extract Skill for first extractor.",
    "game_skill_cpu_management.png": "Engineering skills -> CPU Management; right-click -> Extract Skill for both extractors.",
    "game_skill_weapon_upgrades.png": "Engineering skills -> Weapon Upgrades; right-click -> Extract Skill for second extractor.",
    "game_extract_skill_button.png": "Skill row context menu -> Extract Skill.",
    "game_big_extract_button.png": "Extractor window -> большая кнопка Extract.",
    "game_claim_button.png": "Final Log Off -> claim 10 000 ISK.",
    "game_large_skill_injector.png": "Inventory/Jita 4 -> Large Skill Injector item.",
    "game_create_contract.png": "Right click Large Skill Injector -> Create Contract.",
    "game_private.png": "Contract wizard -> Private contract option.",
    "game_name.png": "Contract wizard -> recipient/name field.",
    "game_search_by.png": "Contract wizard -> Search By label; click to the right of this label.",
    "game_exact_phrase_main.png": "Contract wizard -> primary Exact Phrase option.",
    "game_exact_phrase.png": "Contract wizard -> backup Exact Phrase option.",
    "game_only_exact_phrase.png": "Contract wizard -> Only Exact Phrase option.",
    "game_next_button.png": "Contract wizard -> Next button.",
    "game_type_box.png": "Contract wizard after first Next -> Type checkbox row; click the small square, not the Type text.",
    "game_finish_button.png": "Contract wizard -> Finish button.",
    "game_yes_button.png": "Contract wizard -> final Yes confirmation.",
    "success_screen.png": "Contract wizard -> success screen after final Yes.",
    "game_quit_game_button.png": "Esc menu -> Quit Game.",
    "game_yes_button_after_quit.png": "Quit Game -> Yes confirmation.",
    "game_undock_button.png": "Станция загружена -> Undock button.",
    "game_bottom_neocom_indicator.png": "Нижний Neocom/game UI anchor.",
    "game_top_left_status_indicator.png": "Верхний левый статус/game UI anchor.",
    "game_ui_setting.png": "Esc menu -> User Interface settings.",
    "game_enable_window_blur.png": "Esc -> User Interface -> Enable window blur.",
    "game_new_event.png": "Optional event popup after login.",
    "game_new_event_close_button.png": "New event popup -> close.",
    "game_alpha_status_close_button.png": "Alpha/Omega status popup -> close.",
    "game_alpa_status_downgrade_event.png": "Alpha status downgrade popup.",
    "game_reward_popup_title.png": "Old reward popup title; verify if still used before replacing.",
    "game_activate_skill_extractor.png": "Inventory item context menu -> Activate Skill Extractor.",
}


def is_launcher_template(path):
    name = path.name.lower()
    return "launcher" in name or "lancher" in name


def collect_templates(include_all_screens=False, include_unused=False):
    screens_dir = resource_path("screens")
    all_templates = {
        path.name: path
        for path in sorted(screens_dir.glob("*.png"))
        if include_all_screens or not is_launcher_template(path)
    }
    templates = []
    seen = set()
    for name in SCRIPT_FLOW_TEMPLATE_ORDER:
        path = all_templates.get(name)
        if path:
            templates.append(path)
            seen.add(name)

    if include_unused:
        for name, path in sorted(all_templates.items()):
            if name not in seen:
                templates.append(path)
    return templates


def backup_existing(path, backup_dir):
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def run_clipboard_command(command):
    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout:
        return None
    try:
        return Image.open(io.BytesIO(result.stdout)).convert("RGBA")
    except Exception:
        return None


def image_from_clipboard():
    try:
        grabbed = ImageGrab.grabclipboard()
        if isinstance(grabbed, Image.Image):
            return grabbed.convert("RGBA"), "PIL.ImageGrab"
        if isinstance(grabbed, list) and grabbed:
            for item in grabbed:
                path = Path(item)
                if path.exists():
                    return Image.open(path).convert("RGBA"), f"file:{path}"
    except Exception:
        pass

    commands = [
        ["wl-paste", "--type", "image/png"],
        ["wl-paste", "--type", "image/jpeg"],
        ["wl-paste", "--type", "image/bmp"],
        ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
        ["xclip", "-selection", "clipboard", "-t", "image/jpeg", "-o"],
        ["xclip", "-selection", "clipboard", "-t", "image/bmp", "-o"],
    ]
    for command in commands:
        image = run_clipboard_command(command)
        if image is not None:
            return image, command[0]

    return None, None


def photo_for_image(image, max_size):
    preview = image.copy()
    preview.thumbnail(max_size)
    return ImageTk.PhotoImage(preview)


def template_hint(path):
    return FLOW_HINTS.get(path.name, "Открой в игре состояние, где виден этот элемент, сделай crop screenshot в clipboard и вставь сюда.")


class ManualRecaptureApp:
    def __init__(self, root, templates, backup_dir, output_log):
        self.root = root
        self.templates = templates
        self.backup_dir = resource_path(backup_dir)
        self.output_log = resource_path(output_log)
        self.index = 0
        self.current_template = None
        self.current_original = None
        self.pasted_image = None
        self.original_photo = None
        self.paste_photo = None

        self.status_var = StringVar(value="")
        self.size_var = StringVar(value="")
        self.counter_var = StringVar(value="")
        self.name_var = StringVar(value="")

        self.root.title("EVE Template Recapture")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = max(900, screen_width // 2)
        window_height = max(700, screen_height - 80)
        self.root.geometry(f"{window_width}x{window_height}+0+0")
        self.root.minsize(820, 640)

        self.build_ui()
        self.load_current()

    def build_ui(self):
        header = Frame(self.root, bg="#1f2933")
        header.pack(side=TOP, fill=X)

        title = Label(header, text="EVE template recapture", fg="white", bg="#1f2933", font=("TkDefaultFont", 12, "bold"))
        title.pack(side=LEFT, padx=10, pady=6)

        Label(header, textvariable=self.counter_var, fg="#cbd5e1", bg="#1f2933").pack(side=LEFT, padx=18)

        main = Frame(self.root)
        main.pack(fill=BOTH, expand=True, padx=10, pady=10)

        left = Frame(main)
        left.pack(side=LEFT, fill=BOTH, expand=True)

        right = Frame(main)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=(12, 0))

        Label(left, textvariable=self.name_var, font=("TkDefaultFont", 11, "bold"), anchor="w").pack(fill=X)
        self.original_label = Label(left, text="", relief="groove", width=42, height=14, bg="#111827")
        self.original_label.pack(fill=BOTH, expand=True, pady=(8, 8))

        Label(left, text="Flow / где найти:", anchor="w", font=("TkDefaultFont", 10, "bold")).pack(fill=X)
        self.flow_text = Text(left, height=5, wrap="word")
        self.flow_text.pack(fill=X)
        self.flow_text.configure(state=DISABLED)

        Label(right, text="Paste screenshot here (Ctrl+V) или кнопка Paste:", anchor="w", font=("TkDefaultFont", 10, "bold")).pack(fill=X)
        self.paste_area = Label(right, text="Clipboard image not pasted yet", relief="groove", width=42, height=14, bg="#0f172a", fg="#cbd5e1")
        self.paste_area.pack(fill=BOTH, expand=True, pady=(8, 8))
        self.paste_area.bind("<Control-v>", self.paste_from_clipboard)
        self.paste_area.bind("<Button-1>", lambda _event: self.paste_area.focus_set())
        self.paste_area.focus_set()
        self.root.bind("<Control-v>", self.paste_from_clipboard)

        Label(right, textvariable=self.size_var, anchor="w").pack(fill=X)

        notes_frame = Frame(right)
        notes_frame.pack(fill=X, pady=(8, 0))
        Label(notes_frame, text="Note/problem:", anchor="w").pack(fill=X)
        self.note_text = Text(notes_frame, height=3, wrap="word")
        self.note_text.pack(fill=X)

        controls = Frame(self.root)
        controls.pack(side=BOTTOM, fill=X, padx=10, pady=(0, 10))

        Button(controls, text="Paste", command=self.paste_from_clipboard).pack(side=LEFT, padx=(0, 6))
        Button(controls, text="Done", command=self.done_current).pack(side=LEFT, padx=6)
        Button(controls, text="Skip", command=self.skip_current).pack(side=LEFT, padx=6)
        Button(controls, text="Problem", command=self.problem_current).pack(side=LEFT, padx=6)

        Label(self.root, textvariable=self.status_var, anchor="w").pack(side=BOTTOM, fill=X, padx=10, pady=(0, 6))

    def set_flow_text(self, value):
        self.flow_text.configure(state=NORMAL)
        self.flow_text.delete("1.0", END)
        self.flow_text.insert("1.0", value)
        self.flow_text.configure(state=DISABLED)

    def load_current(self):
        if not self.templates:
            self.name_var.set("No templates")
            self.counter_var.set("0 / 0")
            self.status_var.set("No templates found.")
            return

        self.current_template = self.templates[self.index]
        self.current_original = Image.open(self.current_template).convert("RGBA")
        self.pasted_image = None
        self.original_photo = photo_for_image(self.current_original, MAX_PREVIEW_SIZE)
        self.original_label.configure(image=self.original_photo, text="")
        self.paste_area.configure(image="", text="Clipboard image not pasted yet")
        self.paste_photo = None
        self.note_text.delete("1.0", END)

        relative_name = self.current_template.relative_to(resource_path("."))
        self.name_var.set(str(relative_name))
        self.counter_var.set(f"{self.index + 1} / {len(self.templates)}")
        self.size_var.set(f"Original: {self.current_original.width}x{self.current_original.height}")
        self.set_flow_text(template_hint(self.current_template))
        self.status_var.set("Find this element in game with blur disabled, crop screenshot to clipboard, paste, then Done.")

    def paste_from_clipboard(self, _event=None):
        image, source = image_from_clipboard()
        if image is None:
            self.status_var.set("Clipboard image not found. Try crop screenshot to clipboard, then Ctrl+V/Paste.")
            return "break"

        self.pasted_image = image
        self.paste_photo = photo_for_image(image, MAX_PASTE_PREVIEW_SIZE)
        self.paste_area.configure(image=self.paste_photo, text="")
        warning = ""
        if self.current_original and (
            image.width > self.current_original.width * 5 or image.height > self.current_original.height * 5
        ):
            warning = " WARNING: pasted image is much larger than original; likely full-screen, not crop."
        self.size_var.set(
            f"Original: {self.current_original.width}x{self.current_original.height} | "
            f"Pasted: {image.width}x{image.height} via {source}.{warning}"
        )
        self.status_var.set("Image pasted. Press Done to replace this template with backup.")
        return "break"

    def log_decision(self, action, replacement_path=None, backup_path=None):
        self.output_log.parent.mkdir(parents=True, exist_ok=True)
        note = self.note_text.get("1.0", END).strip()
        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "action": action,
            "template": str(self.current_template.relative_to(resource_path("."))),
            "replacement": str(replacement_path) if replacement_path else None,
            "backup": str(backup_path) if backup_path else None,
            "note": note,
        }
        with self.output_log.open("a", encoding="utf-8") as file:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def done_current(self):
        if self.pasted_image is None:
            self.status_var.set("Nothing pasted. Paste a screenshot first, or use Skip/Problem.")
            return

        backup_path = backup_existing(self.current_template, self.backup_dir)
        self.pasted_image.save(self.current_template)
        self.log_decision("done", replacement_path=self.current_template, backup_path=backup_path)
        self.status_var.set(f"Saved {self.current_template.name}; backup: {backup_path}")
        self.advance()

    def skip_current(self):
        self.log_decision("skip")
        self.status_var.set(f"Skipped {self.current_template.name}")
        self.advance()

    def problem_current(self):
        self.log_decision("problem")
        self.status_var.set(f"Marked problem: {self.current_template.name}")
        self.advance()

    def advance(self):
        if self.index + 1 >= len(self.templates):
            self.status_var.set("Done: reached end of template list.")
            messagebox.showinfo("Done", "Reached end of template list.")
            return
        self.index += 1
        self.load_current()


def main():
    parser = argparse.ArgumentParser(description="Manual EVE template recapture helper.")
    parser.add_argument("--include-launcher", action="store_true", help="Include launcher/lancher templates too.")
    parser.add_argument("--include-unused", action="store_true", help="Append non-launcher screens that are not used in the current script flow.")
    parser.add_argument("--start", help="Start at template filename or relative path.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--log", type=Path, default=DEFAULT_OUTPUT_LOG)
    args = parser.parse_args()

    templates = collect_templates(include_all_screens=args.include_launcher, include_unused=args.include_unused)
    if args.start:
        wanted = args.start.lower()
        for index, path in enumerate(templates):
            if wanted in str(path.relative_to(resource_path("."))).lower() or wanted == path.name.lower():
                templates = templates[index:]
                break
        else:
            raise SystemExit(f"Start template not found: {args.start}")

    root = Tk()
    ManualRecaptureApp(root, templates, args.backup_dir, args.log)
    root.mainloop()


if __name__ == "__main__":
    main()
