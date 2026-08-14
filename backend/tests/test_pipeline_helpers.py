from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app.pipeline.chunking import chunk_text
from app.pipeline.cleaning import clean
from app.schemas import ChatRequest, RunRequest


class RequestValidationTests(unittest.TestCase):
    def test_empty_url_uses_default(self):
        self.assertIsNone(RunRequest(url="   ").url)

    def test_rejects_non_http_and_private_urls(self):
        for value in (
            "not-a-url",
            "file:///etc/passwd",
            "http://localhost/test",
            "http://127.0.0.1/test",
            "http://10.0.0.1/test",
        ):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                RunRequest(url=value)

    @patch(
        "app.schemas.socket.getaddrinfo",
        return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    def test_normalizes_public_url(self, _getaddrinfo):
        request = RunRequest(url=" HTTPS://EXAMPLE.COM/path#fragment ")
        self.assertEqual(request.url, "https://example.com/path")

    @patch(
        "app.schemas.socket.getaddrinfo",
        return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", 443))
        ],
    )
    def test_rejects_domain_resolving_to_private_address(self, _getaddrinfo):
        with self.assertRaises(ValidationError):
            RunRequest(url="https://internal.example/")

    def test_chat_request_strips_question_and_validates_limit(self):
        request = ChatRequest(question="  Kaj je Etrel?  ", limit=3)
        self.assertEqual(request.question, "Kaj je Etrel?")
        with self.assertRaises(ValidationError):
            ChatRequest(question="   ", limit=3)
        with self.assertRaises(ValidationError):
            ChatRequest(question="test", limit=0)


class TextPipelineTests(unittest.TestCase):
    def test_clean_and_chunk_text(self):
        repeated = "To je dovolj dolg ponovljen stavek za odstranjevanje podvajanj."
        self.assertEqual(clean(f" {repeated}   {repeated} "), repeated)

        chunks = chunk_text("Prvi stavek. Drugi stavek. Tretji stavek.", 25, 5)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
