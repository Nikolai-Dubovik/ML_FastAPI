import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Единая настройка логов сервиса: вызывается один раз при старте приложения."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        # force=True — перебиваем настройку, которую мог сделать uvicorn, чтобы формат был один
        force=True,
    )
