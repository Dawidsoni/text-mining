import itertools
from collections import defaultdict

import utils
import argparse

from index_type import IndexType
from posting_list import PostingList
from index_storage import IndexStorage


def _create_traditional_index(wiki_articles, use_terms_clusters=False):
    words_base_forms = utils.read_words_base_forms()
    terms_identifiers = utils.get_terms_identifiers(use_terms_clusters)
    terms_posting_lists = defaultdict(lambda: PostingList())
    for wiki_article in sorted(wiki_articles, key=lambda x: x.id):
        list_of_base_forms = utils.get_base_forms_from_article(words_base_forms, wiki_article)
        article_base_forms = set(itertools.chain(*list_of_base_forms))
        for base_form in article_base_forms:
            terms_posting_lists[terms_identifiers[base_form]].append_if_not_equal_to_last_element(wiki_article.id)
    return {"terms_posting_lists": terms_posting_lists}


def _create_positional_index(wiki_articles, use_terms_clusters=False):
    words_base_forms = utils.read_words_base_forms()
    terms_identifiers = utils.get_terms_identifiers(use_terms_clusters)
    terms_posting_lists = defaultdict(lambda: PostingList())
    position_counter = 1
    documents_positions = []
    for wiki_article in sorted(wiki_articles, key=lambda x: x.id):
        list_of_base_forms = utils.get_base_forms_from_article(words_base_forms, wiki_article)
        documents_positions.append(position_counter)
        for base_forms in list_of_base_forms:
            for term in base_forms:
                terms_posting_lists[terms_identifiers[term]].append_if_not_equal_to_last_element(position_counter)
            position_counter += 1
        position_counter += 1
    return {"terms_posting_lists": terms_posting_lists, "documents_positions": documents_positions}


def _create_index(index_type, wiki_articles, use_terms_clusters):
    if index_type == IndexType.TRADITIONAL:
        return _create_traditional_index(wiki_articles, use_terms_clusters)
    elif index_type == IndexType.POSITIONAL:
        return _create_positional_index(wiki_articles, use_terms_clusters)
    else:
        raise ValueError(f"Invalid index_type: {index_type}")


def _parse_input_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-index_type", type=IndexType, choices=list(IndexType.__dict__.values()))
    parser.add_argument("--use_terms_clusters", type=bool, default=False)
    return vars(parser.parse_args())


def _save_index_data(index_data, index_storage, logger):
    logger.info("Saving posting lists to index storage")
    for term, posting_list in index_data["terms_posting_lists"].items():
        index_storage.add_indexed_term(term, posting_list)
    logger.info("Saving documents positions to index storage")
    if "documents_positions" in index_data:
        for document_position in index_data["documents_positions"]:
            index_storage.add_document_position(document_position)


def run_index_creator(index_type, use_terms_clusters):
    logger = utils.get_default_logger()
    logger.info("Creating index storage...")
    logger.info("Reading wiki articles...")
    wiki_articles = utils.read_wiki_articles()
    logger.info("Creating index...")
    index_data = _create_index(index_type, wiki_articles, use_terms_clusters)
    with IndexStorage(index_type, use_terms_clusters, truncate_old=True) as index_storage:
        logger.info("Saving wiki articles to index storage")
        for wiki_article in wiki_articles:
            index_storage.add_wiki_article(wiki_article)
        _save_index_data(index_data, index_storage, logger)
        logger.info("Saving words base forms to index storage")
        words_base_forms = utils.read_words_base_forms()
        for word, base_forms in words_base_forms.items():
            index_storage.add_word_base_forms(word, base_forms)
    logger.info("Index created successfully")


if __name__ == '__main__':
    run_index_creator(**_parse_input_arguments())
