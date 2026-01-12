import logging
import logging.config
from pathlib import Path

import yaml
from rich.logging import RichHandler


def configure_logging(verbose: bool = False) -> None:
    # Try loading from logging.yaml
    # We assume app/config/logging.yaml relative to source
    # app/src/vtx_app/config -> app/src/vtx_app -> app/src -> app -> config
    # Actually root/config/logging.yaml

    # Let's find project root dynamically or relative to file
    # This file is vtx_app/config/log.py
    # Root is ../../../config/logging.yaml

    base_dir = Path(__file__).resolve().parents[3]
    config_path = base_dir / "config" / "logging.yaml"

    if config_path.exists() and config_path.stat().st_size > 0:
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            return
        except Exception as e:
            logging.error(f"Failed to load logging config: {e}")

    # Fallback / Default
    level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )

    # Quiet down distinct libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
