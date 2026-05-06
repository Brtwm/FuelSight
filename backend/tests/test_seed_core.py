from __future__ import annotations

from app.core.config import Settings
from app.scripts import seed_core


def test_seed_demo_users_flag_defaults_to_enabled() -> None:
    assert seed_core.should_seed_demo_users(Settings()) is True


def test_seed_demo_users_flag_can_disable_demo_accounts() -> None:
    assert seed_core.should_seed_demo_users(Settings(fuelsight_seed_demo_users=False)) is False
