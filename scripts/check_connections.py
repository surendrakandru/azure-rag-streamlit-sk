from src.embeddings import get_embedding


def main():
    text = "Python is used for data science."

    print("Testing Azure OpenAI embeddings...")

    vector = get_embedding(text)

    print("Embedding generated successfully.")
    print(f"Number of dimensions: {len(vector)}")
    print(f"First five values: {vector[:5]}")


if __name__ == "__main__":
    main()