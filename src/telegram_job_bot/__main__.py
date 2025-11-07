"""Entry point for running the Telegram bot."""

from __future__ import annotations

from . import Settings, create_application


def main() -> None:
    settings = Settings()
    application = create_application(settings)
    application.run_polling()


if __name__ == "__main__":
    main()
