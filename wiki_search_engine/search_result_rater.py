import itertools
from collections import defaultdict

import numpy as np


class SearchResultRater(object):
    ID_RATING_FALL_RATE = 1e-5

    def __init__(self, index_storage, query_words_base_forms):
        self.index_storage = index_storage
        self.query_words_base_forms = dict(query_words_base_forms)

    def _get_title_rating(self, title):
        all_title_words = set(map(lambda x: x.lower(), title.lower().split(" ")))
        title_words_base_forms = {
            word: base_forms if len(base_forms) > 0 else [word]
            for word, base_forms in self.index_storage.get_words_base_forms(all_title_words).items()
        }
        query_base_forms = set(itertools.chain(*self.query_words_base_forms.values()))
        rating = 0.0
        for title_word in all_title_words:
            word_base_forms = title_words_base_forms[title_word]
            if any([word_base_form in query_base_forms for word_base_form in word_base_forms]):
                rating += 30
        return rating

    def _get_content_rating(self, content):
        all_content_words = set(map(lambda x: x.lower(), content.lower().split(" ")))
        all_query_words = set(self.query_words_base_forms.keys())
        return float(len(all_content_words.intersection(all_query_words))) * 3

    def _get_article_id_rating(self, article_id):
        return np.exp(-article_id * self.ID_RATING_FALL_RATE)

    def _get_phrases_rating(self, text, weight_of_rating):
        words_in_text = text.lower().split(" ")
        words_base_forms = defaultdict(lambda: {}, self.index_storage.get_words_base_forms(words_in_text))
        last_words_matched_count = 0
        rating = 0.0
        query_base_forms = set(itertools.chain(*self.query_words_base_forms.values()))
        for word in words_in_text:
            intersected_forms = set(words_base_forms[word]).intersection(query_base_forms)
            if len(intersected_forms) > 0:
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


