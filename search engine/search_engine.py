from quotes_index import QuotesIndex
import utils
import termcolor


def _print_matching_quote(quotes_index, query, quote):
    base_forms = quotes_index.generate_base_forms(query)
    for word in quote.split(" "):
        word_base_forms = quotes_index.generate_base_forms(word)
        if len(word_base_forms & base_forms) > 0:
            print(termcolor.colored(f"{word} ", "blue"), end="")
        else:
            print(f"{word} ", end="")
    print("\n")


def run_search_engine():
    print("Creating search engine index")
    words_base_forms = utils.read_words_base_forms()
    quotes = utils.read_quotes()
    quotes_index = QuotesIndex(words_base_forms, quotes)
    print("Type query:")
    query = input()
    matching_quotes = quotes_index.query_index(query)
    for quote in matching_quotes:
        _print_matching_quote(quotes_index, query, quote)


if __name__ == '__main__':
    run_search_engine()

