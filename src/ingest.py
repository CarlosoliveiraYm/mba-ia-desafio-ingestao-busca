#!/usr/bin/env python3

import os
import shutil
import traceback
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

PDF_PATH_INPUT = os.getenv("PDF_PATH_INPUT")
PDF_PATH_PROCESSED = os.getenv("PDF_PATH_PROCESSED")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL")
PG_VECTOR_URL = os.getenv("PG_VECTOR_URL")
PG_VECTOR_COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")

for k in (
    "PDF_PATH_INPUT",
    "PDF_PATH_PROCESSED",
    "OPENAI_EMBEDDING_MODEL",
    "PG_VECTOR_URL",
    "PG_VECTOR_COLLECTION_NAME",
):
    if not os.getenv(k):
        raise RuntimeError(f"Variável de ambiente {k} não está definida.")


def ingest_pdf():
    os.makedirs(PDF_PATH_PROCESSED, exist_ok=True)

    # listar os arquivos PDF no diretório de entrada
    pdf_files = [f for f in os.listdir(PDF_PATH_INPUT) if f.endswith(".pdf")]
    # Verificar se há arquivos PDF para processar
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado na pasta de entrada.")
        return

    # Processar cada arquivo PDF encontrado na pasta de entrada
    for pdf_file in pdf_files:
        print(f"Processando arquivo: {pdf_file}")
        loader = PyPDFLoader(os.path.join(PDF_PATH_INPUT, pdf_file))
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            add_start_index=False,
        )

        chunks = splitter.split_documents(docs)
        if not chunks:
            raise RuntimeError(f"Falha ao processar o arquivo {pdf_file}. Verifique o conteúdo do PDF.")

        # Salvar os dados processados no postgres usando PGVector
        save_vector(chunks, pdf_file)

        # Mover o arquivo PDF processado para a pasta de processados
        shutil.move(
            os.path.join(PDF_PATH_INPUT, pdf_file),
            os.path.join(PDF_PATH_PROCESSED, pdf_file),
        )

    print("Processamento concluído. Todos os arquivos PDF foram processados e movidos para a pasta de processados.")


# Salvar os dados processados no postgres usando PGVector
def save_vector(chunks, pdf_file_name):
    enriched = [
        Document(
            page_content=d.page_content,
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)},
        )
        for d in chunks
    ]

    # IDs únicos evitam colisão quando múltiplos PDFs ou múltiplas execuções são ingeridos.
    ids = [f"{pdf_file_name}-{i}-{uuid4().hex}" for i in range(len(enriched))]

    embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

    store = PGVector(
        embeddings=embeddings,
        collection_name=PG_VECTOR_COLLECTION_NAME,
        connection=PG_VECTOR_URL,
        use_jsonb=True,
    )

    store.add_documents(documents=enriched, ids=ids)


if __name__ == "__main__":
    try:
        ingest_pdf()
    except Exception as e:
        print(f"Ocorreu um erro durante o processamento: {e}")
        traceback.print_exc()