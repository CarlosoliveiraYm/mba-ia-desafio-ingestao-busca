import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import search


class TestSearchSmoke(unittest.TestCase):
    def test_empty_question_returns_default_message(self):
        answer, results = search.search_prompt("")
        self.assertEqual(
            answer,
            "Não tenho informações necessárias para responder sua pergunta.",
        )
        self.assertEqual(results, [])

    def test_uses_top_k_10_by_default_and_returns_llm_content(self):
        fake_doc = SimpleNamespace(page_content="faturamento 10M", metadata={"source": "doc.pdf"})
        fake_results = [(fake_doc, 0.42)]

        fake_store = SimpleNamespace(
            similarity_search_with_score=lambda question, k: fake_results
            if k == 10 and question == "qual faturamento"
            else []
        )
        fake_llm = SimpleNamespace(invoke=lambda prompt: SimpleNamespace(content="resposta mock"))

        with patch.object(search, "_get_store", return_value=fake_store), patch.object(
            search, "_get_llm", return_value=fake_llm
        ), patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SEARCH_TOP_K", None)
            answer, results = search.search_prompt("qual faturamento")

        self.assertEqual(answer, "resposta mock")
        self.assertEqual(results, fake_results)


if __name__ == "__main__":
    unittest.main()
