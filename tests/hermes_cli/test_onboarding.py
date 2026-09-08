"""Tests for the Lexi turnkey onboarding wizard and intake configuration."""

import pytest
from pathlib import Path
from hermes_cli.onboarding import _apply_onboarding_config
from hermes_cli.config import load_config
from hermes_constants import get_hermes_home


def test_apply_onboarding_config_writes_expected_files(tmp_path, monkeypatch):
    home = tmp_path / ".lexi"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("LEXI_HOME", str(home))

    _apply_onboarding_config(
        user_name="Peter",
        timezone="America/Chicago",
        location="Chicago, IL",
        tone="executive",
        vllm_url="http://localhost:8000/v1",
        vllm_model="gemma-4-12b-int4",
        vllm_api_key="EMPTY",
        tg_token="123456:ABC-DEF",
        tg_allowed_users="987654321",
        morning_brief="08:30",
        evening_recap="17:30",
    )

    # 1. Verify config.yaml
    cfg = load_config()
    model_val = cfg.get("model")
    assert model_val == "gemma-4-12b-int4" or (isinstance(model_val, dict) and model_val.get("default") == "gemma-4-12b-int4")
    assert cfg.get("providers", {}).get("custom", {}).get("base_url") == "http://localhost:8000/v1"
    assert cfg["custom_providers"]["vllm"]["base_url"] == "http://localhost:8000/v1"
    assert cfg["custom_providers"]["vllm"]["model"] == "gemma-4-12b-int4"
    assert cfg["custom_providers"]["vllm"]["max_context"] == 65536
    assert cfg["user"]["name"] == "Peter"
    assert cfg["user"]["timezone"] == "America/Chicago"
    assert cfg["user"]["morning_brief"] == "08:30"
    assert cfg["user"]["evening_recap"] == "17:30"

    # 2. Verify SOUL.md
    soul_file = home / "SOUL.md"
    assert soul_file.exists()
    soul_content = soul_file.read_text(encoding="utf-8")
    assert "Lexi" in soul_content
    assert "Peter" in soul_content
    assert "Executive Virtual Personal Assistant" in soul_content

    # 3. Verify USER_PROFILE.md
    profile_file = home / "USER_PROFILE.md"
    assert profile_file.exists()
    profile_content = profile_file.read_text(encoding="utf-8")
    assert "Peter" in profile_content
    assert "America/Chicago" in profile_content
    assert "08:30" in profile_content

    # 4. Verify .env for Telegram
    env_file = home / ".env"
    assert env_file.exists()
    env_content = env_file.read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN=123456:ABC-DEF" in env_content
    assert "TELEGRAM_ALLOWED_USERS=987654321" in env_content
