"""Telegram job recommendation bot package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .config import Settings

if TYPE_CHECKING:  # pragma: no cover
    from .bot import create_application as _create_application


def create_application(settings: Settings):
    """Factory wrapper that avoids importing heavy telegram dependencies eagerly."""

    from .bot import create_application as _create_application

    return _create_application(settings)


__all__ = ["Settings", "create_application"]
