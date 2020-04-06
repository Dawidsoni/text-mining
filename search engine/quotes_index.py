import string
from collections import defaultdict


class QuotesIndex(object):

    def __init__(self, words_base_forms, quotes):
        self.words_base_forms = words_base_forms
        self.quotes = quotes
        self.index_of_quotes = self._generate_index_of_quotes()

    @staticmethod
    def _clear_punctuation(word):
        return ''.join(filter(lambda x: x not in string.punctuation, word))

    def _generate_index_of_quotes(self):
        index_of_quotes = defaultdict(lambda: set())
        for index, quote in enumerate(self.quotes):
            base_forms = self.generate_base_forms(quote)
            for base_form in base_forms:
                index_of_quotes[base_form].add(index)
        return index_of_quotes

    def generate_base_forms(self, sentence):
        words = sentence.split(' ')
        base_forms = []
        for word in words:
            if word in self.words_base_forms:
                base_forms.extend(self.words_base_forms[word])
            else:
                base_forms.append(word)
        return set(base_forms)

    def generate_matching_quotes_indexes(self, query):
        words = query.split(" ")
        word_base_forms = {x: self.generate_base_forms(x) for x in words}
        query_parts = []
        for word, base_forms in word_base_forms.items():
            formatted_forms = map(
                lambda x: f"index['{self._clear_punctuation(x)}']",
                base_forms
            )
            joined_base_forms = " | ".join(formatted_forms)
            query_parts.append(f"({joined_base_forms})")
        generated_query = " & ".join(query_parts)
        return eval(generated_query, {"index": self.index_of_quotes})

    def query_index(self, query):
        matching_indexes = self.generate_matching_quotes_indexes(query)
        return list(map(lambda x: self.quotes[x], matching_indexes))
