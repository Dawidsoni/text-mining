import re
import attr


@attr.s(frozen=True)
class WikiArticle(object):
    id = attr.ib()
    title = attr.ib()
    content = attr.ib()


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
