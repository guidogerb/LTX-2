from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv


def load_env(*, project_env_path: Path | None = None) -> None:
    """
    Environment layering:
      1) OS env already present
      2) config/global.env
      3) config/models.env
      4) project.env (overrides)
    """
    app_root = Path(__file__).resolve().parents[3]  # .../app
    global_env = app_root / "config" / "global.env"
    models_env = app_root / "config" / "models.env"

    # Load global then models without overriding OS env
    if global_env.exists():
        load_dotenv(global_env, override=False)
    if models_env.exists():
        load_dotenv(models_env, override=False)

    # Project overrides last
    if project_env_path and project_env_path.exists():
        load_dotenv(project_env_path, override=True)


def get_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}
