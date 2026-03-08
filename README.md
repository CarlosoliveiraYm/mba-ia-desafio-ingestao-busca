# Desafio MBA Engenharia de Software com IA - Full Cycle

## Verificar se o Python 3 esta instalado (versao 3.12+) e com alias configurado
python --version

## Iniciar ambiente Python e instalar as dependencias
python -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt


## Iniciar PostgreSQL local
docker compose up -d

## Parar PostgreSQL local
docker compose down

## Parar e remover o volume do PostgreSQL local
docker compose down -v

## Rodar testes smoke
python -m unittest discover -s tests -v



## Ordem de execução:

    1. Subir o banco de dados:
    python src/ingest.py

    2. Script de busca
    python src/search.py

    3. Rodar o chat:
    python src/chat.py


