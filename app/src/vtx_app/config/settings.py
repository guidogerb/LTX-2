from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from vtx_app.config.env_layers import get_bool


@dataclass(frozen=True)
class Settings:
    # App/global
    app_home: Path
    projects_root: Path
    default_pipeline: str
    produce_in_acts: bool
    max_parallel_jobs: int
    fail_fast: bool

    # OpenAI (optional story/prompt generation)
    openai_model: str
    openai_max_output_tokens: int
    openai_temperature: float

    # Models (shared)
    checkpoint_path: str | None
    distilled_lora_path: str | None
    spatial_upsampler_path: str | None
    gemma_root: str | None
    ic_lora_path: str | None

    # Practical constraints / defaults
    ltx_max_frames: int
    default_fps: int
    default_max_seconds: int
    default_width: int
    default_height: int

    @staticmethod
    def from_env() -> "Settings":
        app_home = Path(os.getenv("VTX_APP_HOME", "packages/app/_global"))
        projects_root = Path(os.getenv("VTX_PROJECTS_ROOT", "packages/app/projects"))

        return Settings(
            app_home=app_home,
            projects_root=projects_root,
            default_pipeline=os.getenv("VTX_DEFAULT_PIPELINE", "ti2vid_two_stages"),
            produce_in_acts=get_bool("VTX_PRODUCE_IN_ACTS", False),
            max_parallel_jobs=int(os.getenv("VTX_MAX_PARALLEL_JOBS", "1")),
            fail_fast=get_bool("VTX_FAIL_FAST", False),

            # OpenAI
            openai_model=os.getenv("VTX_OPENAI_MODEL", "gpt-4o-2024-08-06"),
            openai_max_output_tokens=int(os.getenv("VTX_OPENAI_MAX_OUTPUT_TOKENS", "4096")),
            openai_temperature=float(os.getenv("VTX_OPENAI_TEMPERATURE", "0.4")),

            # Shared model locations
            checkpoint_path=os.getenv("LTX_CHECKPOINT_PATH"),
            distilled_lora_path=os.getenv("LTX_DISTILLED_LORA_PATH"),
            spatial_upsampler_path=os.getenv("LTX_SPATIAL_UPSAMPLER_PATH"),
            gemma_root=os.getenv("LTX_GEMMA_ROOT"),
            ic_lora_path=os.getenv("LTX_IC_LORA_PATH"),

            ltx_max_frames=int(os.getenv("LTX_MAX_FRAMES", "257")),
            default_fps=int(os.getenv("LTX_DEFAULT_FPS", "16")),
            default_max_seconds=int(os.getenv("LTX_DEFAULT_MAX_SECONDS", "15")),
            default_width=int(os.getenv("LTX_DEFAULT_WIDTH", "1536")),
            default_height=int(os.getenv("LTX_DEFAULT_HEIGHT", "864")),
        )
