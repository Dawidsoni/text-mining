import itertools
from collections import defaultdict

import numpy as np


class SearchResultRater(object):
    ID_RATING_FALL_RATE = 1e-5

    def __init__(self, index_storage, terms_identifiers, query_identifiers):
        self.index_storage = index_storage
        self.terms_identifiers = terms_identifiers
        self.query_identifiers = query_identifiers

    def _get_matching_identifiers(self, text):
        matching_words = set(text.lower().split(" "))
        matching_words_base_forms = {
            word: base_forms if len(base_forms) > 0 else [word]
            for word, base_forms in self.index_storage.get_words_base_forms(matching_words).items()
        }
        matching_base_forms = set(itertools.chain(*matching_words_base_forms.values()))
        return {self.terms_identifiers[x] for x in matching_base_forms}

    def _get_title_rating(self, title):
        matching_identifiers = self._get_matching_identifiers(title)
        return len(matching_identifiers.intersection(self.query_identifiers)) * 30

    def _get_content_rating(self, content):
        matching_identifiers = self._get_matching_identifiers(content)
        return len(matching_identifiers.intersection(self.query_identifiers)) * 5

    def _get_article_id_rating(self, article_id):
        return np.exp(-article_id * self.ID_RATING_FALL_RATE)

    def _get_phrases_rating(self, text, weight_of_rating):
        words_in_text = text.lower().split(" ")
        words_base_forms = defaultdict(lambda: {}, self.index_storage.get_words_base_forms(words_in_text))
        last_words_matched_count = 0
        rating = 0.0
        for word in words_in_text:
            word_identifiers = {self.terms_identifiers[base_form] for base_form in words_base_forms[word]}
            intersected_identifiers = word_identifiers.intersection(self.query_identifiers)
            if len(intersected_identifiers) > 0:
                rating += last_words_matched_count * weight_of_rating
                last_words_matched_count += 1
            else:
                last_words_matched_count = 0
        return rating

    def rate_wiki_article(self, wiki_article):
        title_rating = self._get_title_rating(wiki_article.title)
        content_rating = self._get_content_rating(wiki_article.content)
        article_id_rating = self._get_article_id_rating(wiki_article.id)
        title_phrases_rating = self._get_phrases_rating(wiki_article.title, weight_of_rating=100)
        content_phrases_rating = self._get_phrases_rating(wiki_article.content, weight_of_rating=10)
        return title_rating + content_rating + article_id_rating + title_phrases_rating + content_phrases_rating


