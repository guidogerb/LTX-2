from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import requests
from rich.progress import (BarColumn, DownloadColumn, Progress, TextColumn,
                           TimeRemainingColumn, TransferSpeedColumn)

from vtx_app.config.settings import Settings


@dataclass
class ModelSpec:
    env_var_name: str
    url: str
    sha256: str
    filename: str


# Define known models and their sources
# Note: These are example URLs/Hashes. In a real scenario, these must be accurate.
# For now, I will add placeholders or generic structure that can be updated.
KNOWN_MODELS: list[ModelSpec] = [
    ModelSpec(
        env_var_name="LTX_CHECKPOINT_PATH",
        url="https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.1.safetensors",
        sha256="ec6d4f9b876f2f0d9c1f6b3e8c8a1b9d5e3c7a0f1d5e3c7a0f1d5e3c7a0f1d5e",  # Placeholder hash
        filename="checkpoint.safetensors",
    ),
    ModelSpec(
        env_var_name="LTX_DISTILLED_LORA_PATH",
        url="https://civital.com/api/download/models/12345",  # Placeholder
        sha256="0000000000000000000000000000000000000000000000000000000000000000",
        filename="distilled_lora.safetensors",
    ),
    # Add others as needed
]


class ModelDownloader:
    def __init__(self, settings: Settings):
        self.settings = settings

    def ensure_model(self, env_var_name: str) -> Path | None:
        """
        Checks if the model configured by env_var_name exists.
        If not, downloads it if a definition exists in KNOWN_MODELS.
        Returns the path to the model.
        """
        # 1. Get the configured path from settings
        # We need to map env_var_name back to the settings attribute
        # But settings attributes are already resolved values (str | None).

        # We can look up the value using getattr if we know the attribute name map
        # Or just read os.environ directly for the path since settings is immutable
        path_str = os.getenv(env_var_name)

        if not path_str:
            print(
                f"[yellow]Skipping download for {env_var_name}: Variable not set.[/yellow]"
            )
            return None

        path = Path(path_str)
        if path.exists():
            return path

        # 2. Find the spec
        spec = next((m for m in KNOWN_MODELS if m.env_var_name == env_var_name), None)
        if not spec:
            print(
                f"[red]Model missing at {path} and no download spec found for {env_var_name}.[/red]"
            )
            raise FileNotFoundError(f"Missing model: {path}")

        # 3. Download
        return self._download_and_verify(spec, path)

    def _download_and_verify(self, spec: ModelSpec, dest: Path) -> Path:
        print(
            f"[bold cyan]Downloading missing model for {spec.env_var_name}...[/bold cyan]"
        )
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Prepare headers (e.g. for CivitAI or HF Auth)
        headers = {}
        if "civitai" in spec.url:
            api_key = os.getenv("CIVITAI_API_KEY")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        elif "huggingface" in spec.url:
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                headers["Authorization"] = f"Bearer {hf_token}"

        # Download with stream
        temp_dest = dest.with_suffix(".tmp")
        try:
            with requests.get(spec.url, headers=headers, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))

                with Progress(
                    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    "•",
                    DownloadColumn(),
                    "•",
                    TransferSpeedColumn(),
                    "•",
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task(
                        "download", filename=spec.filename, total=total_size
                    )
                    with open(temp_dest, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))

            # Verify
            print("Verifying SHA256...")
            file_hash = self._calculate_sha256(temp_dest)
            if spec.sha256 != "SKIP" and file_hash != spec.sha256:
                print(
                    f"[red]Hash mismatch! Expected {spec.sha256}, got {file_hash}[/red]"
                )
                # In strict mode we might delete. specific use case might want to keep it.
                # raising error to trigger retry or stop.
                raise ValueError(f"Hash mismatch for {spec.filename}")

            shutil.move(str(temp_dest), str(dest))
            print(f"[green]Successfully installed {spec.filename}[/green]")
            return dest

        except Exception as e:
            if temp_dest.exists():
                temp_dest.unlink()
            raise e

    def _calculate_sha256(self, path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
