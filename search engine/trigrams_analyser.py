from collections import defaultdict
from quotes_index import QuotesIndex
import utils


def run_trigrams_analyser():
    words_base_forms = utils.read_words_base_forms()
    quotes = utils.read_quotes()
    quotes_index = QuotesIndex(words_base_forms, quotes)
    trigrams = utils.read_trigrams()
    trigram_quotes_indexes = {
        x: tuple(sorted(quotes_index.generate_matching_quotes_indexes(x)))
        for x in trigrams
    }
    equivalence_classes = defaultdict(lambda: [])
    for trigram, quotes_indexes in trigram_quotes_indexes.items():
        equivalence_classes[quotes_indexes].append(trigram)
    for equivalence_class, trigrams in equivalence_classes.items():
        for trigram in trigrams:
            print(trigram)
        print("\n")


if __name__ == '__main__':
    run_trigrams_analyser()
