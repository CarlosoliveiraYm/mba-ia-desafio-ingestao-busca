from search import search_prompt


def main():
    print("Chat iniciado. Digite sua pergunta ou 'sair' para encerrar.\n")

    while True:
        try:
            question = input("Você: ").strip()
        except KeyboardInterrupt:
            print("\nEncerrando chat.")
            break

        if question.lower() in {"sair", "exit", "quit"}:
            print("Encerrando chat.")
            break

        try:
            answer, results = search_prompt(question)
        except Exception as exc:
            print(f"\nErro ao processar pergunta: {exc}\n")
            continue

        print(f"\nAssistente: {answer}\n")

        if results:
            print("Contexto usado:")
            for i, (_, score) in enumerate(results, start=1):
                print(f"- Trecho {i} | score: {score:.4f}")
            print()

if __name__ == "__main__":
    main()