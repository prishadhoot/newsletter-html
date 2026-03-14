"""
Tests for newsletter-html: template filling, response validation, and API mocking.
Run from repo root: python -m pytest tests.py -v   or   python tests.py
This is for the old codebase and may need to be modified for the current state
"""
import json
import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Minimal template so main can load without utils/templates/response_template.json
_RESPONSE_TEMPLATE = {
    "past_24_hours": {
        "24h_1": "", "24h_2": "", "24h_3": "",
        "24h_4": "", "24h_5": "", "24h_6": "",
    },
    "whats_going_viral": {"viral_1": "", "viral_2": "", "viral_3": ""},
    "innovations_and_developments": {"company_developments": ""},
}


def _mock_main_open(path, *args, **kwargs):
    if "response_template.json" in path:
        return mock_open(read_data=json.dumps(_RESPONSE_TEMPLATE))()
    raise FileNotFoundError(path)


@patch("os.path.exists", return_value=True)
@patch("builtins.open", side_effect=lambda path, *a, **k: _mock_main_open(path, *a, **k))
def _import_main(mock_exists, mock_open_func):
    import main as m
    return m


class TestTemplateFilling(unittest.TestCase):
    """Test fill_template and placeholder replacement."""

    @classmethod
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=lambda path, *a, **k: _mock_main_open(path, *a, **k))
    def setUpClass(cls, mock_exists, mock_open_func):
        cls.main = _import_main(mock_exists, mock_open_func)

    def test_fill_template_replaces_24h_placeholders(self):
        template = "<li>{24h_1}</li><li>{24h_2}</li>"
        data = {
            "past_24_hours": {"24h_1": "News A", "24h_2": "News B"},
            "whats_going_viral": {"viral_1": "", "viral_2": "", "viral_3": ""},
            "innovations_and_developments": {"company_developments": ""},
        }
        # Ensure all keys exist for the loop in fill_template (1..6 and 1..3)
        for i in range(1, 7):
            data["past_24_hours"].setdefault(f"24h_{i}", "")
        for i in range(1, 4):
            data["whats_going_viral"].setdefault(f"viral_{i}", "")
        out = self.main.fill_template(template, data)
        self.assertIn("News A", out)
        self.assertIn("News B", out)
        self.assertNotIn("{24h_1}", out)

    def test_fill_template_replaces_viral_and_company_placeholders(self):
        template = "<p>{viral_1}</p><p>{company_developments}</p>"
        data = {
            "past_24_hours": {f"24h_{i}": "" for i in range(1, 7)},
            "whats_going_viral": {"viral_1": "Viral topic", "viral_2": "", "viral_3": ""},
            "innovations_and_developments": {"company_developments": "Company summary."},
        }
        out = self.main.fill_template(template, data)
        self.assertIn("Viral topic", out)
        self.assertIn("Company summary.", out)
        self.assertNotIn("{viral_1}", out)
        self.assertNotIn("{company_developments}", out)


class TestResponseValidation(unittest.TestCase):
    """Test is_matching and validate_and_correct."""

    @classmethod
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=lambda path, *a, **k: _mock_main_open(path, *a, **k))
    def setUpClass(cls, mock_exists, mock_open_func):
        cls.main = _import_main(mock_exists, mock_open_func)

    def test_is_matching_true_when_structure_matches(self):
        template = {"a": {"b": ""}, "c": ""}
        response = {"a": {"b": "x"}, "c": "y"}
        self.assertTrue(self.main.is_matching(response, template))

    def test_is_matching_false_when_key_missing(self):
        template = {"a": "", "b": ""}
        response = {"a": "x"}
        self.assertFalse(self.main.is_matching(response, template))

    def test_is_matching_false_when_nested_type_wrong(self):
        template = {"a": {"b": ""}}
        response = {"a": "not a dict"}
        self.assertFalse(self.main.is_matching(response, template))

    def test_validate_and_correct_fills_missing_keys_from_template(self):
        template = {"past_24_hours": {"24h_1": "default"}, "extra": "fallback"}
        response = {"past_24_hours": {"24h_1": "custom"}}
        out = self.main.validate_and_correct(response, template)
        self.assertEqual(out["past_24_hours"]["24h_1"], "custom")
        self.assertEqual(out["extra"], "fallback")

    def test_validate_and_correct_recursive(self):
        template = {"nested": {"a": "t1", "b": "t2"}}
        response = {"nested": {"a": "r1"}}
        out = self.main.validate_and_correct(response, template)
        self.assertEqual(out["nested"]["a"], "r1")
        self.assertEqual(out["nested"]["b"], "t2")


class TestProcessResponse(unittest.TestCase):
    """Test process_response with valid/invalid JSON and structure."""

    @classmethod
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=lambda path, *a, **k: _mock_main_open(path, *a, **k))
    def setUpClass(cls, mock_exists, mock_open_func):
        cls.main = _import_main(mock_exists, mock_open_func)

    def test_process_response_valid_matching_json_returns_unchanged(self):
        data = dict(_RESPONSE_TEMPLATE)
        data["past_24_hours"]["24h_1"] = "Headline"
        raw = json.dumps(data)
        out = self.main.process_response(raw)
        parsed = json.loads(out)
        self.assertEqual(parsed["past_24_hours"]["24h_1"], "Headline")

    def test_process_response_invalid_json_returns_template_fallback(self):
        out = self.main.process_response("not valid json {{{")
        parsed = json.loads(out)
        self.assertIn("past_24_hours", parsed)
        self.assertIn("whats_going_viral", parsed)
        self.assertIn("innovations_and_developments", parsed)

    def test_process_response_missing_keys_corrected_to_template(self):
        data = {"past_24_hours": {"24h_1": "only"}}
        out = self.main.process_response(json.dumps(data))
        parsed = json.loads(out)
        self.assertIn("whats_going_viral", parsed)
        self.assertIn("innovations_and_developments", parsed)


class TestFetchTechNews(unittest.TestCase):
    """Test fetch_tech_news with mocked Perplexity API."""

    @classmethod
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", side_effect=lambda path, *a, **k: _mock_main_open(path, *a, **k))
    def setUpClass(cls, mock_exists, mock_open_func):
        cls.main = _import_main(mock_exists, mock_open_func)

    @patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}, clear=False)
    @patch("requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data="Summarize tech news.")
    def test_fetch_tech_news_returns_parsed_data_on_200(self, mock_file, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "past_24_hours": {f"24h_{i}": f"News {i}" for i in range(1, 7)},
                            "whats_going_viral": {"viral_1": "V1", "viral_2": "V2", "viral_3": "V3"},
                            "innovations_and_developments": {"company_developments": "Devs"},
                        })
                    }
                }
            ]
        }
        result = self.main.fetch_tech_news()
        self.assertIsNotNone(result)
        self.assertEqual(result.past_24_hours.h24_1, "News 1")
        self.assertEqual(result.innovations_and_developments.company_developments, "Devs")

    @patch.dict(os.environ, {}, clear=True)
    def test_fetch_tech_news_raises_without_api_key(self):
        with self.assertRaises(ValueError):
            self.main.fetch_tech_news()


if __name__ == "__main__":
    unittest.main()
