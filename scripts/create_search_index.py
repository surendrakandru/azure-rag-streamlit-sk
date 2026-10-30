from src.search_index import create_search_index


def main():
    print("Setting up Azure AI Search index...")
    result = create_search_index()
    print(result)


if __name__ == "__main__":
    main()