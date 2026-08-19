from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app.pipeline.chunking import chunk_text
from app.pipeline.cleaning import clean
from app.pipeline.extraction_context import build_extraction_text, page_excerpt
from app.schemas import ChatRequest, RunRequest
from scraper.scraper.spiders.keywords import HIGH_PRIORITY_KEYWORDS, KEYWORDS


class RequestValidationTests(unittest.TestCase):
    def test_empty_url_uses_default(self):
        self.assertIsNone(RunRequest(url="   ").url)

    def test_run_settings_are_bounded(self):
        request = RunRequest(max_depth=0, max_pages=200, chunk_size=300)
        self.assertEqual(request.max_depth, 0)
        self.assertEqual(request.max_pages, 200)
        self.assertEqual(request.chunk_size, 300)

        for values in (
            {"max_depth": -1},
            {"max_depth": 6},
            {"max_pages": 0},
            {"max_pages": 201},
            {"chunk_size": 299},
            {"chunk_size": 4001},
        ):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                RunRequest(**values)

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
        self.assertEqual(request.scope, "latest")
        self.assertEqual(ChatRequest(question="test", scope="all").scope, "all")
        with self.assertRaises(ValidationError):
            ChatRequest(question="   ", limit=3)
        with self.assertRaises(ValidationError):
            ChatRequest(question="test", limit=0)
        with self.assertRaises(ValidationError):
            ChatRequest(question="test", scope="invalid")


class TextPipelineTests(unittest.TestCase):
    def test_clean_and_chunk_text(self):
        repeated = "To je dovolj dolg ponovljen stavek za odstranjevanje podvajanj."
        self.assertEqual(clean(f" {repeated}   {repeated} "), repeated)

        chunks = chunk_text("Prvi stavek. Drugi stavek. Tretji stavek.", 25, 5)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk for chunk in chunks))

    def test_extraction_excerpt_keeps_leadership_near_end_of_long_page(self):
        text = "Uvodna predstavitev podjetja. " + ("Splošna vsebina. " * 300)
        text += "Lovrenc Švegl je CEO podjetja."

        excerpt = page_excerpt(text, 1200)

        self.assertLessEqual(len(excerpt), 1200)
        self.assertIn("Lovrenc Švegl", excerpt)
        self.assertIn("CEO", excerpt)

    def test_extraction_context_reserves_space_for_management_page(self):
        pages = [
            {
                "url": "https://example.com/",
                "depth": 0,
                "text": "Domača stran. " + ("Predstavitev. " * 500),
            },
            {
                "url": "https://example.com/privacy-policy/",
                "depth": 1,
                "text": "Pravilnik zasebnosti. " * 1000,
            },
            {
                "url": "https://example.com/o-podjetju/vodstvo/",
                "depth": 2,
                "text": "Vodstvo Družbo vodi Jože Primer, predsednik uprave.",
            },
            {
                "url": "https://example.com/zgodovina/",
                "depth": 1,
                "text": "Podjetje je bilo ustanovljeno leta 1989.",
            },
        ]

        context = build_extraction_text(pages, max_chars=6000)

        self.assertLessEqual(len(context), 6000)
        self.assertIn("Jože Primer", context)
        self.assertIn("ustanovljeno leta 1989", context)
        self.assertIn("[VIR: https://example.com/o-podjetju/vodstvo/]", context)

    def test_fei_management_urls_are_prioritized_by_scraper(self):
        for keyword in ("o_fakulteti", "poslovodstvo", "organiziranost", "organi"):
            self.assertIn(keyword, KEYWORDS)
            self.assertIn(keyword, HIGH_PRIORITY_KEYWORDS)


if __name__ == "__main__":
    unittest.main()
