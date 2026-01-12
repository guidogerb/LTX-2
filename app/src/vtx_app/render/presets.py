from typing import Any

PRESETS = {
    "low": {
        "width": 480,
        "height": 270,
        "fps": 12,
        "num_inference_steps": 20,
    },
    "medium": {
        "width": 768,
        "height": 432,
        "fps": 24,
        "num_inference_steps": 30,
    },
    "high": {
        "width": 1280,
        "height": 720,
        "fps": 24,
        "num_inference_steps": 50,
    },
    "ultra": {
        "width": 1920,
        "height": 1080,
        "fps": 24,
        "num_inference_steps": 60,
    },
}


def get_preset(name: str) -> dict[str, Any]:
    return PRESETS.get(name, {})
