"""
Unit tests for NLP Query Parser.

Tests the natural language query parsing functionality.
"""

import json
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

from src.nlp_query_parser import NLPQueryParser, ParsedQuery
from src.errors import ArcGISValidationError


class TestNLPQueryParser(unittest.TestCase):
    """Test suite for NLPQueryParser."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock API key for tests
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

    def test_initialization_without_api_key(self):
        """Test that initialization fails without API key."""
        del os.environ["ANTHROPIC_API_KEY"]

        with self.assertRaises(ArcGISValidationError) as context:
            NLPQueryParser()

        self.assertIn("API key required", str(context.exception))

        # Restore for other tests
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

    def test_initialization_with_api_key_param(self):
        """Test initialization with explicit API key."""
        parser = NLPQueryParser(api_key="explicit-key")
        self.assertEqual(parser.api_key, "explicit-key")

    def test_initialization_with_env_api_key(self):
        """Test initialization with environment variable API key."""
        parser = NLPQueryParser()
        self.assertEqual(parser.api_key, "test-key")

    def test_parse_empty_query(self):
        """Test that parsing empty query raises error."""
        parser = NLPQueryParser(api_key="test-key")

        with self.assertRaises(ArcGISValidationError):
            parser.parse("")

        with self.assertRaises(ArcGISValidationError):
            parser.parse("   ")

    def test_get_supported_queries(self):
        """Test getting supported query examples."""
        examples = NLPQueryParser.get_supported_queries()

        self.assertIsInstance(examples, list)
        self.assertGreater(len(examples), 0)

        for example in examples:
            self.assertIn("natural_language", example)
            self.assertIn("where_clause", example)
            self.assertIn("description", example)

    def test_get_field_mappings(self):
        """Test getting field mappings."""
        mappings = NLPQueryParser.get_field_mappings()

        self.assertIsInstance(mappings, dict)
        self.assertGreater(len(mappings), 0)

        # Check some expected mappings
        self.assertEqual(mappings.get("state"), "STATE_NAME")
        self.assertEqual(mappings.get("county"), "NAME")
        self.assertEqual(mappings.get("area"), "SQMI")
        self.assertEqual(mappings.get("population"), "POPULATION")

    @patch('src.nlp_query_parser.Anthropic')
    def test_parse_simple_query(self, mock_anthropic):
        """Test parsing a simple natural language query."""
        # Mock Claude API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "where_clause": "STATE_NAME = 'Texas' AND SQMI < 2500",
            "confidence": 0.95,
            "explanation": "Filtering Texas counties with area under 2500 square miles",
            "detected_fields": ["STATE_NAME", "SQMI"]
        }))]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        parser = NLPQueryParser(api_key="test-key")
        result = parser.parse("find counties in Texas under 2500 square miles")

        self.assertIsInstance(result, ParsedQuery)
        self.assertEqual(result.where_clause, "STATE_NAME = 'Texas' AND SQMI < 2500")
        self.assertEqual(result.confidence, 0.95)
        self.assertIn("STATE_NAME", result.detected_fields)
        self.assertIn("SQMI", result.detected_fields)

    @patch('src.nlp_query_parser.Anthropic')
    def test_parse_with_markdown_code_blocks(self, mock_anthropic):
        """Test parsing response with markdown code blocks."""
        # Mock Claude API response with markdown
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=f"""```json
{json.dumps({
    "where_clause": "STATE_NAME = 'California'",
    "confidence": 0.90,
    "explanation": "Simple state filter",
    "detected_fields": ["STATE_NAME"]
})}
```""")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        parser = NLPQueryParser(api_key="test-key")
        result = parser.parse("counties in California")

        self.assertIsInstance(result, ParsedQuery)
        self.assertEqual(result.where_clause, "STATE_NAME = 'California'")

    @patch('src.nlp_query_parser.Anthropic')
    def test_parse_multiple_states(self, mock_anthropic):
        """Test parsing query with multiple states."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "where_clause": "STATE_NAME IN ('Texas', 'Oklahoma')",
            "confidence": 0.92,
            "explanation": "Multiple state selection using IN clause",
            "detected_fields": ["STATE_NAME"]
        }))]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        parser = NLPQueryParser(api_key="test-key")
        result = parser.parse("show me counties in Texas or Oklahoma")

        self.assertIn("IN", result.where_clause)
        self.assertIn("Texas", result.where_clause)
        self.assertIn("Oklahoma", result.where_clause)

    @patch('src.nlp_query_parser.Anthropic')
    def test_parse_range_query(self, mock_anthropic):
        """Test parsing a range query."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "where_clause": "STATE_NAME = 'Texas' AND SQMI >= 1000 AND SQMI <= 3000",
            "confidence": 0.94,
            "explanation": "Range query for counties between 1000 and 3000 square miles",
            "detected_fields": ["STATE_NAME", "SQMI"]
        }))]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        parser = NLPQueryParser(api_key="test-key")
        result = parser.parse("counties in Texas between 1000 and 3000 square miles")

        self.assertIn(">=", result.where_clause)
        self.assertIn("<=", result.where_clause)
        self.assertIn("1000", result.where_clause)
        self.assertIn("3000", result.where_clause)

    @patch('src.nlp_query_parser.Anthropic')
    def test_parse_population_query(self, mock_anthropic):
        """Test parsing a population-based query."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "where_clause": "STATE_NAME = 'California' AND POPULATION > 1000000",
            "confidence": 0.96,
            "explanation": "California counties with population over 1 million",
            "detected_fields": ["STATE_NAME", "POPULATION"]
        }))]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        parser = NLPQueryParser(api_key="test-key")
        result = parser.parse("counties in California with population over 1 million")

        self.assertIn("POPULATION", result.where_clause)
        self.assertIn("1000000", result.where_clause)

    @patch('src.nlp_query_parser.Anthropic')
    def test_parse_api_error(self, mock_anthropic):
        """Test handling of API errors."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        parser = NLPQueryParser(api_key="test-key")

        with self.assertRaises(ArcGISValidationError) as context:
            parser.parse("find counties in Texas")

        self.assertIn("Failed to parse query", str(context.exception))

    @patch('src.nlp_query_parser.Anthropic')
    def test_parse_invalid_json_response(self, mock_anthropic):
        """Test handling of invalid JSON in response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not valid JSON")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        parser = NLPQueryParser(api_key="test-key")

        with self.assertRaises(ArcGISValidationError) as context:
            parser.parse("find counties in Texas")

        self.assertIn("Failed to parse query", str(context.exception))

    @patch('src.nlp_query_parser.Anthropic')
    def test_build_prompt(self, mock_anthropic):
        """Test prompt building includes necessary information."""
        mock_anthropic.return_value = MagicMock()

        parser = NLPQueryParser(api_key="test-key")
        prompt = parser._build_prompt("test query")

        # Check prompt contains key information
        self.assertIn("USA Census Counties", prompt)
        self.assertIn("STATE_NAME", prompt)
        self.assertIn("SQMI", prompt)
        self.assertIn("test query", prompt)
        self.assertIn("JSON", prompt)
        self.assertIn("where_clause", prompt)

    def test_parsed_query_dataclass(self):
        """Test ParsedQuery dataclass."""
        result = ParsedQuery(
            where_clause="STATE_NAME = 'Texas'",
            confidence=0.95,
            explanation="Test explanation",
            detected_fields=["STATE_NAME"]
        )

        self.assertEqual(result.where_clause, "STATE_NAME = 'Texas'")
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.explanation, "Test explanation")
        self.assertEqual(result.detected_fields, ["STATE_NAME"])

    def test_field_mappings_immutability(self):
        """Test that field mappings cannot be modified."""
        mappings1 = NLPQueryParser.get_field_mappings()
        mappings2 = NLPQueryParser.get_field_mappings()

        # Modify one copy
        mappings1["test"] = "TEST_FIELD"

        # Original should be unchanged
        self.assertNotIn("test", mappings2)

    def test_supported_queries_immutability(self):
        """Test that supported queries cannot be modified."""
        queries1 = NLPQueryParser.get_supported_queries()
        queries2 = NLPQueryParser.get_supported_queries()

        # Modify one copy
        queries1.append({"test": "data"})

        # Original should be unchanged
        self.assertNotEqual(len(queries1), len(queries2))


class TestParsedQuery(unittest.TestCase):
    """Test ParsedQuery dataclass."""

    def test_create_parsed_query(self):
        """Test creating a ParsedQuery instance."""
        query = ParsedQuery(
            where_clause="STATE_NAME = 'Texas'",
            confidence=0.95,
            explanation="Filtering by state",
            detected_fields=["STATE_NAME"]
        )

        self.assertEqual(query.where_clause, "STATE_NAME = 'Texas'")
        self.assertEqual(query.confidence, 0.95)
        self.assertEqual(query.explanation, "Filtering by state")
        self.assertEqual(query.detected_fields, ["STATE_NAME"])

    def test_parsed_query_with_empty_fields(self):
        """Test ParsedQuery with empty detected fields."""
        query = ParsedQuery(
            where_clause="1=1",
            confidence=1.0,
            explanation="Match all",
            detected_fields=[]
        )

        self.assertEqual(query.detected_fields, [])


if __name__ == "__main__":
    unittest.main()
