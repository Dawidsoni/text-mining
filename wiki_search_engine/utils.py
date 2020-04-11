import re
import logging
import itertools
from collections import defaultdict
from wiki_article import WikiArticle


def _create_wiki_article(article_id, parsed_article):
    article_parts = parsed_article.split("\n\n")
    title = re.search("TITLE: (.*)", article_parts[0].strip()).group(1)
    content = "\n".join(article_parts[1:])
    return WikiArticle(id=article_id, title=title, content=content)


def read_wiki_articles():
    with open("data/wiki_slice.txt") as stream:
        merged_lines = "\n".join(stream.readlines())
        parsed_articles = merged_lines.split("\n\n\n")
        return list(map(
            lambda index_x: _create_wiki_article(index_x[0] + 1, index_x[1]),
            enumerate(parsed_articles)
        ))


def read_words_base_forms():
    words_base_forms = defaultdict(lambda: [])
    with open("data/base_forms.txt", "r") as stream:
        bases_words = map(lambda x: x.split(";")[0:2], stream.readlines())
        for base, word in bases_words:
            words_base_forms[word].append(base)
    return words_base_forms


def get_default_logger():
    logging.basicConfig(format="%(levelname)s (%(asctime)s) - %(message)s", level=logging.INFO)
    return logging.getLogger("DEFAULT_LOGGER")


def get_base_forms_from_text(words_base_forms, text):
    split_words = set(map(lambda x: x.strip(), text.split(" ")))
    return set(itertools.chain(*map(
        lambda x: words_base_forms[x] if x in words_base_forms else [x],
        split_words
    )))
