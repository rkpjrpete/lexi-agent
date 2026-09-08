"""Lexi Executive Virtual Personal Assistant -- Non-technical Onboarding Wizard.

A guided, turnkey intake process for single/dual-user appliance setups:
- User profile (name, timezone, location, preferred tone)
- Local vLLM inference server (Gemma 4 12B int4, 64k context limit)
- Google Workspace integration (Calendar, Gmail, Contacts)
- Telegram mobile bot setup (optional)
- Daily briefing schedule (morning agenda, evening recap)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from hermes_constants import get_hermes_home
from hermes_cli.config import load_config, save_config, get_config_path
from hermes_cli.banner import LEXI_AGENT_LOGO


def _prompt(text: str, default: str = "") -> str:
    """Read line with optional default value displayed."""
    if default:
        display = f"{text} [{default}]: "
    else:
        display = f"{text}: "
    try:
        val = input(display).strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        print("\n\nSetup cancelled.")
        sys.exit(0)


def _choice(prompt_text: str, options: list[tuple[str, str]], default_idx: int = 0) -> str:
    """Display numbered choices and return the selected key."""
    print(f"\n{prompt_text}")
    for idx, (key, label) in enumerate(options, 1):
        indicator = " (default)" if idx == default_idx + 1 else ""
        print(f"  [{idx}] {label}{indicator}")
    
    while True:
        raw = _prompt("Select option", default=str(default_idx + 1))
        try:
            val = int(raw)
            if 1 <= val <= len(options):
                return options[val - 1][0]
        except ValueError:
            pass
        print(f"Please choose a number between 1 and {len(options)}.")


def run_onboarding_wizard(non_interactive: bool = False) -> None:
    """Run the complete Lexi turnkey intake and setup process."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    console = Console()

    console.print()
    console.print(LEXI_AGENT_LOGO)
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Welcome to Lexi — Your Executive Virtual Personal Assistant[/]\n\n"
            "This turnkey setup will configure your dedicated hardware, personal preferences,\n"
            "local AI inference server (vLLM), Google Workspace, and mobile channels.",
            border_style="cyan"
        )
    )

    if non_interactive:
        console.print("[dim]Running in non-interactive mode with appliance defaults...[/dim]")
        _apply_onboarding_defaults()
        console.print("[green]✔ Lexi is ready with default configuration.[/green]")
        return

    # -------------------------------------------------------------
    # 1. User Identity & Preferences
    # -------------------------------------------------------------
    console.print("\n[bold cyan]Step 1: Your Profile[/bold cyan]")
    user_name = _prompt("Your name / preferred form of address", default="User")
    
    # Auto-detect timezone if possible
    detected_tz = "UTC"
    try:
        if os.path.exists("/etc/timezone"):
            detected_tz = Path("/etc/timezone").read_text(encoding="utf-8").strip()
        elif os.path.exists("/etc/localtime"):
            detected_tz = os.path.realpath("/etc/localtime").split("zoneinfo/")[-1]
    except Exception:
        pass
    
    timezone = _prompt("Your timezone (e.g. America/Chicago, America/New_York, Europe/London)", default=detected_tz)
    location = _prompt("Your city/location (for weather and local time awareness)", default="Chicago, IL")

    tone_choices = [
        ("executive", "Executive & Polished — Crisp, proactive, highly structured, business-ready"),
        ("warm", "Warm & Supportive — Helpful, friendly, thorough, and approachable"),
        ("concise", "Ultra-Concise — Short bullet points, zero small talk, maximum brevity"),
    ]
    selected_tone = _choice("Choose Lexi's communication style:", tone_choices, default_idx=0)

    # -------------------------------------------------------------
    # 2. Local AI Engine (vLLM / Gemma 4 12B int4)
    # -------------------------------------------------------------
    console.print("\n[bold cyan]Step 2: Local AI Inference Server (vLLM)[/bold cyan]")
    console.print("[dim]Configured for 16GB VRAM appliance running Gemma 4 12B int4 with 64k token context.[/dim]")

    vllm_url = _prompt("vLLM API Base URL", default="http://localhost:8000/v1")
    vllm_model = _prompt("Model Name in vLLM", default="gemma-4-12b-int4")
    vllm_api_key = _prompt("API Key (leave blank for local server without auth)", default="EMPTY")

    # -------------------------------------------------------------
    # 3. Google Workspace (Calendar, Gmail, Contacts, Drive)
    # -------------------------------------------------------------
    console.print("\n[bold cyan]Step 3: Google Workspace (Calendar & Gmail)[/bold cyan]")
    console.print("Google integration enables Lexi to manage your schedule, draft emails, and provide daily briefings.")

    google_home = get_hermes_home()
    token_file = google_home / "google_token.json"
    client_secret_file = google_home / "google_client_secret.json"

    has_google = token_file.exists()
    if has_google:
        console.print("[green]✔ Google Workspace credentials detected.[/green]")
    else:
        console.print("[yellow]Notice:[/] Google OAuth client credentials not found yet.")
        console.print("You can connect your Google account now or anytime later by running [bold]lexi tools google-workspace[/bold].")

    # -------------------------------------------------------------
    # 4. Telegram Mobile Access (Optional)
    # -------------------------------------------------------------
    console.print("\n[bold cyan]Step 4: Telegram Mobile Assistant (Optional)[/bold cyan]")
    console.print("Access Lexi on the go securely via Telegram.")
    enable_tg = _prompt("Would you like to connect a Telegram Bot now? (y/N)", default="n").lower() in ("y", "yes")

    tg_token = ""
    tg_allowed_users = ""
    if enable_tg:
        console.print("Create a bot via [bold]@BotFather[/bold] on Telegram and paste your Bot Token:")
        tg_token = _prompt("Telegram Bot Token", default="")
        tg_allowed_users = _prompt("Your Telegram User ID (to restrict bot access to you only, optional)", default="")

    # -------------------------------------------------------------
    # 5. Daily Briefing Routines
    # -------------------------------------------------------------
    console.print("\n[bold cyan]Step 5: Daily Briefings & Schedule[/bold cyan]")
    morning_brief = _prompt("Morning Briefing time (24h format e.g. 08:00, or 'off')", default="08:00")
    evening_recap = _prompt("Evening Wrap-up time (24h format e.g. 18:00, or 'off')", default="18:00")

    # -------------------------------------------------------------
    # Saving Configurations & User Context
    # -------------------------------------------------------------
    console.print("\n[dim]Saving configurations and initializing Lexi's memory...[/dim]")

    _apply_onboarding_config(
        user_name=user_name,
        timezone=timezone,
        location=location,
        tone=selected_tone,
        vllm_url=vllm_url,
        vllm_model=vllm_model,
        vllm_api_key=vllm_api_key,
        tg_token=tg_token,
        tg_allowed_users=tg_allowed_users,
        morning_brief=morning_brief,
        evening_recap=evening_recap,
    )

    console.print()
    console.print(
        Panel.fit(
            f"[bold green]✔ Lexi Setup Complete![/]\n\n"
            f"👤 [bold]User:[/] {user_name} ({location}, {timezone})\n"
            f"🤖 [bold]Model:[/] {vllm_model} via {vllm_url}\n"
            f"📅 [bold]Daily Briefings:[/] Morning at {morning_brief}, Evening at {evening_recap}\n"
            f"📱 [bold]Telegram:[/] {'Connected' if tg_token else 'Not configured (optional)'}\n\n"
            f"[cyan]To start interacting with Lexi:[/]\n"
            f"  • Interactive Chat:      [bold]lexi[/bold]\n"
            f"  • Web Dashboard:         [bold]lexi gateway --web[/bold]\n"
            f"  • Background Services:   [bold]lexi gateway[/bold]\n",
            border_style="green",
        )
    )


def _apply_onboarding_defaults() -> None:
    """Apply standard out-of-the-box appliance defaults."""
    _apply_onboarding_config(
        user_name="User",
        timezone="UTC",
        location="Local",
        tone="executive",
        vllm_url="http://localhost:8000/v1",
        vllm_model="gemma-4-12b-int4",
        vllm_api_key="EMPTY",
        tg_token="",
        tg_allowed_users="",
        morning_brief="08:00",
        evening_recap="18:00",
    )


def _apply_onboarding_config(
    user_name: str,
    timezone: str,
    location: str,
    tone: str,
    vllm_url: str,
    vllm_model: str,
    vllm_api_key: str,
    tg_token: str,
    tg_allowed_users: str,
    morning_brief: str,
    evening_recap: str,
) -> None:
    """Write configuration, SOUL.md, USER_PROFILE.md, and .env."""
    home = get_hermes_home()
    home.mkdir(parents=True, exist_ok=True)

    # 1. Update config.yaml
    cfg = load_config() or {}
    cfg["model"] = vllm_model
    if "providers" not in cfg:
        cfg["providers"] = {}
    cfg["providers"]["custom"] = {
        "base_url": vllm_url,
        "api_key": vllm_api_key or "EMPTY",
    }
    
    # Configure custom/vllm provider
    if "custom_providers" not in cfg:
        cfg["custom_providers"] = {}
    
    cfg["custom_providers"]["vllm"] = {
        "base_url": vllm_url,
        "api_key": vllm_api_key or "EMPTY",
        "model": vllm_model,
        "max_context": 65536,
        "format": "openai",
    }
    
    # Store user preference metadata
    if "user" not in cfg:
        cfg["user"] = {}
    cfg["user"]["name"] = user_name
    cfg["user"]["timezone"] = timezone
    cfg["user"]["location"] = location
    cfg["user"]["tone"] = tone
    cfg["user"]["morning_brief"] = morning_brief
    cfg["user"]["evening_recap"] = evening_recap

    save_config(cfg)

    # 2. Write personalized SOUL.md
    tone_descriptions = {
        "executive": (
            f"You are Lexi, an Executive Virtual Personal Assistant to {user_name}. You are proactive, "
            f"highly organized, discrete, and clear. You manage schedules, emails, tasks, daily briefings, "
            f"and research with executive poise. Be direct: match the length of your reply to the weight of "
            f"the ask — a quick question gets a crisp answer, while meeting prep and briefings are organized "
            f"into structured, actionable points. Confirm destructive actions before executing. Plain claims over "
            f"adjectives; when unsure, state so plainly."
        ),
        "warm": (
            f"You are Lexi, a warm, supportive, and highly capable Executive Personal Assistant to {user_name}. "
            f"You manage {user_name}'s schedule, communications, and daily tasks with attentive care, helpful clarity, "
            f"and proactive organization. Match the length of your reply to the ask, keep summaries structured, "
            f"and confirm critical actions before proceeding."
        ),
        "concise": (
            f"You are Lexi, an ultra-concise Executive Personal Assistant to {user_name}. Provide minimal, structured, "
            f"high-density answers. Use bullet points and action items. Zero small talk or conversational filler. "
            f"Confirm destructive actions before executing."
        ),
    }

    soul_text = tone_descriptions.get(tone, tone_descriptions["executive"])
    (home / "SOUL.md").write_text(soul_text, encoding="utf-8")

    # 3. Write USER_PROFILE.md (persisted for memory / context)
    profile_content = (
        f"# User Profile: {user_name}\n\n"
        f"- **Name / Salutation**: {user_name}\n"
        f"- **Primary Location**: {location}\n"
        f"- **Timezone**: {timezone}\n"
        f"- **Communication Tone**: {tone.capitalize()}\n"
        f"- **Daily Briefing**: {morning_brief}\n"
        f"- **Evening Recap**: {evening_recap}\n"
    )
    (home / "USER_PROFILE.md").write_text(profile_content, encoding="utf-8")

    # 4. Write .env for Telegram if supplied
    env_path = home / ".env"
    existing_env = ""
    if env_path.exists():
        existing_env = env_path.read_text(encoding="utf-8")

    env_lines = [l for l in existing_env.splitlines() if not l.startswith("TELEGRAM_")]
    if tg_token:
        env_lines.append(f"TELEGRAM_BOT_TOKEN={tg_token}")
    if tg_allowed_users:
        env_lines.append(f"TELEGRAM_ALLOWED_USERS={tg_allowed_users}")

    env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
