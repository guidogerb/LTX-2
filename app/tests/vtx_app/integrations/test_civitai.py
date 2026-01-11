from __future__ import annotations

from unittest.mock import Mock, patch

import httpx
import pytest

from vtx_app.integrations.civitai import CivitAIClient


@pytest.fixture
def client():
    return CivitAIClient()


def test_search_loras_success(client):
    mock_response = {
        "items": [
            {
                "name": "Test LoRA",
                "id": 123,
                "modelVersions": [{"downloadUrl": "http://dl/123"}],
                "description": "A test lora",
            }
        ]
    }

    with patch("httpx.Client") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.__enter__.return_value.get.return_value.json.return_value = (
            mock_response
        )
        mock_instance.__enter__.return_value.get.return_value.status_code = 200

        results = client.search_loras("query")

        assert len(results) == 1
        assert results[0]["name"] == "Test LoRA"
        assert results[0]["download_url"] == "http://dl/123"


def test_search_loras_empty_versions(client):
    mock_response = {
        "items": [
            {
                "name": "Test LoRA",
                "id": 123,
                "modelVersions": [],
            }
        ]
    }

    with patch("httpx.Client") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.__enter__.return_value.get.return_value.json.return_value = (
            mock_response
        )

        results = client.search_loras("query")

        assert len(results) == 1
        assert results[0]["download_url"] == ""


def test_search_loras_failure(client):
    with patch("httpx.Client") as MockClient:
        mock_instance = MockClient.return_value
        # mocking get to raise exception
        mock_instance.__enter__.return_value.get.side_effect = httpx.RequestError(
            "fail"
        )

        results = client.search_loras("query")

        assert results == []


def test_search_loras_bad_status(client):
    with patch("httpx.Client") as MockClient:
        mock_instance = MockClient.return_value
        # raise_for_status might be called
        mock_resp = mock_instance.__enter__.return_value.get.return_value
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=Mock(), response=Mock()
        )

        results = client.search_loras("query")
        assert results == []
