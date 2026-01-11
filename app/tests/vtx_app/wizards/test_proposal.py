from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from vtx_app.wizards.proposal import ProposalGenerator


@pytest.fixture
def mock_settings(tmp_path):
    class MockSettings:
        openai_model = "gpt-model"
        app_home = tmp_path

    return MockSettings()


@pytest.fixture
def generator(mock_settings):
    return ProposalGenerator(settings=mock_settings)


def test_analyze_concept_success(generator):
    expected_args = {
        "title": "My Movie",
        "slug": "my_movie",
        "logline": "Log",
        "visual_style_keywords": ["style"],
        "synopsis": "Syn",
    }

    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = json.dumps(expected_args)

    with patch("openai.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.return_value = mock_resp

        result = generator.analyze_concept("Input text")

        assert result == expected_args
        # Verify schema passed
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "response_format" in call_kwargs
        assert (
            call_kwargs["response_format"]["json_schema"]["name"] == "proposal_metadata"
        )


def test_analyze_concept_failure_openai(generator):
    with patch("openai.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.side_effect = Exception("OpenAI Error")

        result = generator.analyze_concept("Input text")

        # Fallback
        assert result["title"] == "Untitled"
        assert result["synopsis"] == "Input text"


def test_analyze_concept_empty_response(generator):
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = ""  # Empty

    with patch("openai.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.return_value = mock_resp

        result = generator.analyze_concept("Input text")

        # Should raise ValueError internally and trigger fallback
        assert result["title"] == "Untitled"


def test_create_proposal_flow(generator):
    # Mock dependencies - note we mock where they are DEFINED because they are local imports
    with patch("vtx_app.tags_manager.TagManager") as MockTM, patch(
        "vtx_app.style_manager.StyleManager"
    ) as MockSM, patch(
        "vtx_app.wizards.proposal.CivitAIClient"
    ) as MockCivit, patch.object(
        generator, "analyze_concept"
    ) as mock_analyze:

        # Setup mocks
        mock_tm = MockTM.return_value
        mock_tm.process_prompt.return_value = (
            "Processed Text [style_preset]"  # returns text with style tag?
        )
        # Actually in code:
        #   concept_text = tm.process_prompt(concept_text)
        #   style_matches = re.finditer...
        # So process_prompt should return text that might have expanded tags.
        # But if we want to test style detection, we should put the style tag in the output.

        mock_tm.process_prompt.side_effect = (
            lambda x: x
        )  # Identity for simplicity or specific expansion

        mock_analyze.return_value = {
            "title": "T",
            "slug": "s",
            "logline": "l",
            "visual_style_keywords": ["k1"],
            "synopsis": "syn",
        }

        mock_sm = MockSM.return_value
        mock_sm.load_style.return_value = {
            "resources": {"bundles": [{"name": "StyleLora"}]}
        }
        mock_sm.get_style_keywords.return_value = ["style_kw"]

        mock_civit = MockCivit.return_value
        mock_civit.search_loras.return_value = [{"name": "SearchLora"}]

        # Run
        # Case 1: Text with style tag
        input_text = "My idea [style_test]"
        proposal = generator.create_proposal(input_text)

        assert proposal["meta"]["title"] == "T"
        assert proposal["meta"]["style_preset"] == "test"

        # Verify style keywords injection
        # analyze_concept was called. logic inside create_proposal merges keywords.
        # Wait, analyze_concept is called with stripped text.
        # Then the RESULT of analyze_concept is modified with style keywords.

        assert "suggested_loras" in proposal["resources"]
        loras = proposal["resources"]["suggested_loras"]
        # Expected: StyleLora (extra) + SearchLora (search result)
        assert any(l["name"] == "StyleLora" for l in loras)

        # NOTE: mock civitai result list order is appended after extra_loras
        assert any(l["name"] == "SearchLora" for l in loras)


def test_create_proposal_legacy_style(generator):
    with patch("vtx_app.tags_manager.TagManager") as MockTM, patch(
        "vtx_app.style_manager.StyleManager"
    ) as MockSM, patch(
        "vtx_app.wizards.proposal.CivitAIClient"
    ) as MockCivit, patch.object(
        generator, "analyze_concept"
    ) as mock_analyze:

        mock_tm = MockTM.return_value
        mock_tm.process_prompt.side_effect = lambda x: x
        mock_analyze.return_value = {
            "title": "T",
            "slug": "s",
            "logline": "l",
            "visual_style_keywords": [],
            "synopsis": "syn",
        }

        mock_sm = MockSM.return_value
        # load_style returns dict if exists, None if not. Dict must be not empty to be True.
        mock_sm.load_style.side_effect = lambda x: (
            {"foo": "bar"} if x == "legacy" else None
        )
        mock_sm.get_style_keywords.return_value = []

        # Legacy format: [style] at start
        text = "[legacy] My idea"
        proposal = generator.create_proposal(text)

        assert proposal["meta"]["style_preset"] == "legacy"


def test_create_proposal_no_style(generator):
    with patch("vtx_app.tags_manager.TagManager") as MockTM, patch(
        "vtx_app.style_manager.StyleManager"
    ) as MockSM, patch(
        "vtx_app.wizards.proposal.CivitAIClient"
    ) as MockCivit, patch.object(
        generator, "analyze_concept"
    ) as mock_analyze:

        mock_tm = MockTM.return_value
        mock_tm.process_prompt.side_effect = lambda x: x
        mock_analyze.return_value = {
            "title": "T",
            "slug": "s",
            "logline": "l",
            "visual_style_keywords": [],
            "synopsis": "syn",
        }

        proposal = generator.create_proposal("Raw text")
        assert "style_preset" not in proposal["meta"]
