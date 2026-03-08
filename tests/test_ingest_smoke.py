import os
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import ingest


class TestIngestSmoke(unittest.TestCase):
    def test_save_vector_generates_unique_ids_per_chunk(self):
        chunks = [
            SimpleNamespace(page_content="A", metadata={"page": 1}),
            SimpleNamespace(page_content="B", metadata={"page": 2}),
            SimpleNamespace(page_content="C", metadata={"page": 3}),
        ]

        captured = {}

        class FakeStore:
            def add_documents(self, documents, ids):
                captured["documents"] = documents
                captured["ids"] = ids

        with patch.object(ingest, "OpenAIEmbeddings", return_value=SimpleNamespace()), patch.object(
            ingest, "PGVector", return_value=FakeStore()
        ):
            ingest.save_vector(chunks, "arquivo.pdf")

        ids = captured["ids"]
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(set(ids)), 3)
        for index, item_id in enumerate(ids):
            self.assertTrue(item_id.startswith(f"arquivo.pdf-{index}-"))
            self.assertRegex(item_id, r"arquivo\.pdf-\d+-[0-9a-f]{32}$")


if __name__ == "__main__":
    unittest.main()
