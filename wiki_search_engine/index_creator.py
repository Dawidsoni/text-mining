from collections import defaultdict

import utils
from posting_list import PostingList
from index_storage import IndexStorage


def _get_base_forms_from_article(words_base_forms, wiki_article):
    merged_words = " ".join([wiki_article.title, wiki_article.content]).lower()
    return utils.get_base_forms_from_text(words_base_forms, merged_words)


def _create_terms_posting_lists(wiki_articles):
    words_base_forms = utils.read_words_base_forms()
    terms_posting_lists = defaultdict(lambda: PostingList())
    for wiki_article in sorted(wiki_articles, key=lambda x: x.id):
        article_base_forms = _get_base_forms_from_article(words_base_forms, wiki_article)
        for base_form in article_base_forms:
            terms_posting_lists[base_form].append(wiki_article.id)
    return terms_posting_lists


def run_index_creator():
    logger = utils.get_default_logger()
    logger.info("Creating index storage...")
    logger.info("Reading wiki articles...")
    wiki_articles = utils.read_wiki_articles()
    logger.info("Creating posting lists")
    terms_posting_lists = _create_terms_posting_lists(wiki_articles)
    with IndexStorage(truncate_old=True) as index_storage:
        logger.info("Saving wiki articles to index storage")
        for wiki_article in wiki_articles:
            index_storage.add_wiki_article(wiki_article)
        logger.info("Saving posting lists to index storage")
        for term, posting_list in terms_posting_lists.items():
            index_storage.add_indexed_term(term, posting_list)
        logger.info("Saving words base forms to index storage")
        words_base_forms = utils.read_words_base_forms()
        for word, base_forms in words_base_forms.items():
            index_storage.add_word_base_forms(word, base_forms)
    logger.info("Index created successfully")


if __name__ == '__main__':
    run_index_creator()
