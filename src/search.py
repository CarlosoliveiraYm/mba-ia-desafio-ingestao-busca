import os
from functools import lru_cache

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def _get_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente {name} não está definida.")
    return value


@lru_cache(maxsize=1)
def _get_store():
    embeddings = OpenAIEmbeddings(model=_get_env("OPENAI_EMBEDDING_MODEL"))
    return PGVector(
        embeddings=embeddings,
        collection_name=_get_env("PG_VECTOR_COLLECTION_NAME"),
        connection=_get_env("PG_VECTOR_URL"),
        use_jsonb=True,
    )


@lru_cache(maxsize=1)
def _get_llm():
    _get_env("OPENAI_API_KEY")
    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=0)


def _build_context_from_results(results):
    parts = []
    for i, (doc, score) in enumerate(results, start=1):
        metadata = ", ".join(f"{k}: {v}" for k, v in doc.metadata.items()) or "sem metadados"
        parts.append(
            f"Trecho {i} (score: {score:.4f})\n"
            f"Metadados: {metadata}\n"
            f"Conteúdo:\n{doc.page_content.strip()}"
        )
    return "\n\n".join(parts)


def search_prompt(question=None):
    if not question or not question.strip():
        return "Não tenho informações necessárias para responder sua pergunta.", []

    # Passo 3: montar o prompt com o contexto recuperado e chamar a LLM.
    top_k = int(os.getenv("SEARCH_TOP_K", "10"))
    results = _get_store().similarity_search_with_score(question, k=top_k)
    if not results:
        return "Não tenho informações necessárias para responder sua pergunta.", []

    contexto = _build_context_from_results(results)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=question)

    response = _get_llm().invoke(prompt)

    # Passo 4: retornar a resposta para o usuário.
    return response.content.strip(), results
