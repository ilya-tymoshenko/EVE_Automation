# EVE Automation Linux Adaptation Plan

## Confirmed Facts
- The directory is not a normal writable git checkout for this session; validate edits by direct reads and targeted checks.
- The current main script is `eve_bot.py`.
- Current automation is an older Python + `pyautogui` flow for adding EVE accounts, signing in, launching the client, creating a new capsuleer, importing a skill plan, and removing the account from the launcher.
- The requested target flow is different: sign into existing SP-farm accounts, claim the free Omega gift, extract skill points, and contract the extractors/items to a main account.
- Linux EVE is installed through Steam at `/home/ilya/.local/share/Steam/steamapps/common/Eve Online`.
- Steam app id for EVE Online is `8500`.
- The old launcher path is Windows-only: `D:\SteamLibrary\steamapps\common\Eve Online\eve-online.exe`.
- Local Python dependencies required by the scripts are installed in `.venv`.
- The current desktop session reports Wayland.
- Runtime import of `pyautogui` needs the local `/dev/null` XAUTHORITY fallback because `/home/ilya/.Xauthority` is absent.
- Screenshot capture works through a local `grim` backend at `2560x1440`.
- Existing images for launcher gift handling exist: `gift_claim_button.png`, `gift_close_button.png`, `confirm_yes_button.png`, `license_accept_button.png`.
- `launcher_play_button.png` currently contains a "Create Capsuleer" button, not a confirmed normal "Play" button for existing characters.
- Runtime image templates are now centralized in `eve_config.MATCH_TEMPLATE_ASSETS`.
- Current runtime templates are: `add_account_button.png`, `sign_in_button.png`, `launcher_play_button.png`, `gift_claim_button.png`, `gift_close_button.png`, `confirm_yes_button.png`, `license_accept_button.png`, `caldari_faction_1.png`, `caldari_faction_2.png`, `caldari_faction_3.png`, `caldari_faction_4.png`, `name.png`, `character_creation_success_indicator.png`.

## Unknowns
- Exact current EVE launcher layout after signing into these existing accounts on Linux.
- Exact screens/coordinates for claiming the 7-day Omega gift in the current launcher build.
- Exact in-game route for buying/using/extracting two skill extractors and creating a contract to the main account.
- The main account/character name for the final contract.
- Whether the current account range and password are still correct.

## Working Plan
1. Make the existing scripts portable enough to run on Linux:
   - remove Windows-only launcher startup as the default on Linux;
   - resolve assets relative to the script directory, not the current shell directory;
   - document/install required Python dependencies.
2. Add a preflight check that reports missing modules, Linux session risks, launcher command, and required assets before any GUI automation starts.
3. Preserve the old character-creation behavior until the new harvest flow is confirmed from live screenshots/coordinates.
4. After the launcher flow is visible on Linux, capture/replace the needed button images:
   - normal "Play" button for existing characters;
   - free Omega claim button/state;
   - any confirmation/close states.
   - Use `template_audit.py` to check current templates against a live or saved screenshot.
   - Use `template_capture.py` to replace a template crop; it backs up the old file under `template_backups/` by default.
5. Implement the new harvest flow as explicit steps with verification after each major action:
   - account login;
   - Omega claim;
   - client launch;
   - extractor handling;
   - contract creation to main account;
   - logout/account cleanup.
6. OpenAI API repair loop:
   - no direct OpenAI API integration inside `eve_bot.py`;
   - the main bot stops on critical/unexpected failures instead of improvising UI actions;
   - failure context is saved as a local crash bundle with screenshot, reason, current account, and log tail;
   - `run_with_codex_repair.py` asks OpenAI Responses API for a structured repair report after a non-zero bot exit;
   - the API runner does not apply generated code changes automatically;
   - the runner validates with preflight before restarting when the report marks restart as safe.

## Current Status
- Done: Linux launcher/config/preflight infrastructure.
- Done: local `.venv` dependency installation.
- Done: Wayland screenshot backend through `grim`.
- Done: replaced the earlier recovery hook with a stop-and-repair runner.
- Done: `eve_bot.py` now writes failure context bundles under `runtime_failures/` on non-user critical stops.
- Done: `run_with_codex_repair.py` can ask OpenAI API for a repair report, validate with preflight, and restart the bot with `EVE_START_ACCOUNT` when restart is safe.
- Done: full runtime template list is included in preflight through `MATCH_TEMPLATE_ASSETS`.
- Done: added `template_audit.py` for screenshot/template score checks.
- Done: added `template_capture.py` for safe crop-based template replacement with backups.
- Not started: real harvest-flow implementation, because the required current UI evidence is not yet available.

## Env Secret Migration Plan

### Confirmed Facts
- `eve_bot.py` currently contains the EVE account password directly in code.
- Gmail OAuth data currently exists in local `credentials.json` and `token.json`.
- There is no existing `.dockerignore`, `.gitignore`, `.env`, or `.env.example` in the repository root.

### Working Plan
1. Load root `.env` values before scripts read project settings.
2. Move EVE account password and Gmail OAuth values to environment variables.
3. Add `.env.example` with variable names but no secret values.
4. Add `.env` and legacy secret JSON files to `.dockerignore` and `.gitignore`.
5. Redact legacy JSON files after local values are migrated to `.env`.
6. Run static checks and scan the code for remaining obvious hardcoded secrets.

### Current Status
- Done: `.env` is loaded from the project root.
- Done: EVE account password and Gmail OAuth values are read from env.
- Done: `.env.example`, `.dockerignore`, and `.gitignore` are added.
- Done: local secrets were migrated into `.env` without printing values.
- Done: legacy `credentials.json` and `token.json` were redacted.
- Done: static parse and secret scans passed.

## OpenAI API Repair Integration Plan

### Confirmed Facts
- `run_with_codex_repair.py` previously invoked `codex exec` after bot failures.
- The existing repair contract is `codex_repair_schema.json`.
- The runner already saves crash context under `runtime_failures/` and report files under `codex_reports/`.

### Working Plan
1. Replace Codex CLI invocation with OpenAI Responses API.
2. Keep the existing JSON report schema as the API structured output contract.
3. Send only sanitized crash context, selected source files, and optional screenshot input to the model.
4. Keep `.env`/tokens/passwords out of prompts, logs, and reports.
5. Do not auto-apply generated code changes in the API runner.
6. Validate with static syntax checks and dry-run behavior.

### Current Status
- Done: `run_with_codex_repair.py` now uses OpenAI Responses API instead of `codex exec`.
- Done: structured output uses the existing `codex_repair_schema.json` contract.
- Done: source context and screenshot input are included when available.
- Done: generated code changes are not auto-applied by the API runner.
- Done: `openai` SDK was added to `requirements.txt` and installed in local `.venv`.

## GitHub Push Rule Cleanup Plan

### Confirmed Facts
- GitHub rejected the first push because repository push rules detected secrets.
- Local reachable history contains secrets in the old initial commit.
- `__pycache__` files are tracked and `__pycache__/eve_bot.cpython-314.pyc` still contains the old hardcoded password.
- The remote `main` branch has not been created yet, so rewriting local `main` before first push is the lowest-risk fix.

### Working Plan
1. Remove tracked `__pycache__` files from git index while keeping local files on disk.
2. Create a new single root commit from the current sanitized tree.
3. Move local `main` to that clean commit.
4. Verify reachable branch history no longer contains the detected secret patterns.
5. Push `main` to GitHub.

### Current Status
- In progress.
