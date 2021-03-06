import re
import logging
from collections import defaultdict
from wiki_article import WikiArticle


class IdentityDictionary(object):
    def __getitem__(self, item):
        return item


def _create_wiki_article(article_id, parsed_article):
    article_parts = parsed_article.split("\n\n")
    title = re.search("TITLE: (.*)", article_parts[0].strip()).group(1)
    content = "\n".join(article_parts[1:])
    return WikiArticle(id=article_id, title=title, content=content)


def read_wiki_articles(path="data/wiki_slice.txt"):
    with open(path) as stream:
        merged_lines = "\n".join(stream.readlines())
        parsed_articles = merged_lines.split("\n\n\n")
        return list(map(
            lambda index_x: _create_wiki_article(index_x[0] + 1, index_x[1]),
            enumerate(parsed_articles)
        ))


def read_words_base_forms(path="data/base_forms.txt"):
    words_base_forms = defaultdict(lambda: [])
    with open(path, "r") as stream:
        bases_words = map(lambda x: x.split(";")[0:2], stream.readlines())
        for base, word in bases_words:
            words_base_forms[word].append(base)
    return words_base_forms


def get_default_logger():
    logging.basicConfig(format="%(levelname)s (%(asctime)s) - %(message)s", level=logging.INFO)
    return logging.getLogger("DEFAULT_LOGGER")


def get_base_forms_from_article(words_base_forms, wiki_article, with_default_word=True):
    merged_words = " ".join([wiki_article.title, wiki_article.content]).lower()
    list_of_base_forms = []
    for word in merged_words.split(" "):
        cleaned_word = word.strip()
        if with_default_word and cleaned_word not in words_base_forms:
            list_of_base_forms.append([cleaned_word])
        elif cleaned_word in words_base_forms:
            list_of_base_forms.append(words_base_forms[cleaned_word])
    return list_of_base_forms


def get_terms_identifiers(use_terms_clusters=False, path="data/terms_clusters_10000.txt"):
    if not use_terms_clusters:
        return IdentityDictionary()
    with open(path) as file_stream:
        lines = [line.strip() for line in file_stream.readlines()]
        terms_identifiers = [(line.split(" ")[0], line.split(" ")[1]) for line in lines]
        return defaultdict(lambda: "0", terms_identifiers)
