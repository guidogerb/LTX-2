from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from rich import print


@dataclass
class CivitAIClient:
    base_url: str = "https://civitai.com/api/v1"

    def search_loras(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """
        Search for LoRAs on CivitAI.
        """
        url = f"{self.base_url}/models"
        params = {
            "query": query,
            "types": "LORA",
            "limit": limit,
            "sort": "Highest Rated",
            "period": "AllTime",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", [])

                results = []
                for item in items:
                    name = item.get("name")
                    model_id = item.get("id")
                    versions = item.get("modelVersions", [])
                    download_url = ""
                    if versions:
                        # Get latest version
                        download_url = versions[0].get("downloadUrl", "")

                    results.append(
                        {
                            "name": name,
                            "url": f"https://civitai.com/models/{model_id}",
                            "download_url": download_url,
                            "description": item.get("description", "")[:200],
                        }
                    )
                return results

        except Exception as e:
            print(f"[yellow]CivitAI search failed:[/yellow] {e}")
            return []
