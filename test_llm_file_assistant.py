import os
import unittest
from unittest.mock import patch

from llm_file_assistant import OPENROUTER_BASE_URL, create_client


class OpenRouterClientTests(unittest.TestCase):
    @patch("llm_file_assistant.load_dotenv")
    @patch("llm_file_assistant.OpenAI")
    def test_create_client_uses_openrouter_endpoint_and_environment_key(
        self, openai_client, load_dotenv
    ):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            client = create_client()

        load_dotenv.assert_called_once()
        self.assertEqual(
            load_dotenv.call_args.args[0].name,
            ".env",
        )
        openai_client.assert_called_once_with(
            base_url=OPENROUTER_BASE_URL,
            api_key="test-key",
        )
        self.assertIs(client, openai_client.return_value)

    @patch("llm_file_assistant.load_dotenv")
    def test_create_client_reports_missing_key(self, load_dotenv):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENROUTER_API_KEY"):
                create_client()


if __name__ == "__main__":
    unittest.main()
