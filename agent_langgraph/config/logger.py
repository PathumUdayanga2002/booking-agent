import logging
from typing import Optional


def _configure_root_logger(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger_name = name if name else "agent_langgraph"
    if not logging.getLogger().handlers:
        _configure_root_logger("INFO")
    return logging.getLogger(logger_name)
