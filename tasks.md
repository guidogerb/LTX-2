# Project Tasks

This file tracks the setup and development tasks for the LTX-2 workspace.

## Setup & installation

- [ ] **Install Flash Attention (GPU Only)**
    - `DreamID-V` requires `flash-attn` for GPU acceleration.
    - Run: `uv install flash-attn` (ensure you have CUDA Toolkit installed).
    - Or install from wheel: verify your torch/cuda version and find the appropriate wheel from [https://github.com/Dao-AILab/flash-attention/releases](https://github.com/Dao-AILab/flash-attention/releases).

- [ ] **Install LTX-2 Models**
    - The `app` requires LTX-2 models.
    - Use the automated downloader: `cd app && uv run vtx_app model download` (or similar command if implemented).
    - Or manually download from HuggingFace (see README).

## DreamID-V Integration

- [ ] **Validate DreamID-V Setup**
    - Run: `uv run python -c "import dreamid_v; print(dreamid_v.__version__)"`
    - Verify `flash_attn` import if on GPU.

- [ ] **Run DreamID-V Inference**
    - Create a script or use provided examples in `DreamID-V` folder.
    - Note: Need to provide a driving video and a source image.

## Development

- [ ] **Run Tests**
    - Root: `uv run pytest`
    - App: `cd app && uv run pytest`

- [ ] **Linting**
    - `uv run ruff check .`
