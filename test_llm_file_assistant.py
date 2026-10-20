import os
import unittest
from unittest.mock import patch

from llm_file_assistant import OPENROUTER_BASE_URL, create_client


class OpenRouterClientTests(unittest.TestCase):
    @patch("llm_file_assistant.OpenAI")
    def test_create_client_uses_openrouter_endpoint_and_environment_key(
        self, openai_client
    ):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            client = create_client()

        openai_client.assert_called_once_with(
            base_url=OPENROUTER_BASE_URL,
            api_key="test-key",
        )
        self.assertIs(client, openai_client.return_value)

    def test_create_client_reports_missing_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENROUTER_API_KEY"):
                create_client()


if __name__ == "__main__":
    unittest.main()
