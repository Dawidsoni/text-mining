import itertools
import logging
from collections import defaultdict

import numpy as np

import utils

from posting_list import PostingList


def _create_terms_posting_lists(coding):
    wiki_articles = utils.read_wiki_articles()
    words_base_forms = utils.read_words_base_forms()
    terms_posting_lists = defaultdict(lambda: PostingList(coding=coding))
    for wiki_article in wiki_articles:
        list_of_base_forms = utils.get_base_forms_from_article(words_base_forms, wiki_article, with_default_word=False)
        article_base_forms = set(itertools.chain(*list_of_base_forms))
        for base_form in article_base_forms:
            terms_posting_lists[base_form].append(wiki_article.id)
    return terms_posting_lists.values()


def _count_bytes_in_postings_lists(posting_lists):
    return sum([len(posting_list.coded_sequence) for posting_list in posting_lists])


def _count_int32_bytes_in_ordered_lists(ordered_lists):
    return sum([len(ordered_list.items) * 4 for ordered_list in ordered_lists])


def _count_bytes_in_gamma_coding_list(ordered_list):
    last_value = 0
    total_bits = 0
    for value in ordered_list:
        increase_of_value = value - last_value
        if increase_of_value == 0:
            continue
        total_bits += 2 * np.floor(np.log2(increase_of_value)) + 1
        last_value = value
    return int(np.ceil(total_bits / 8))


def _count_bytes_in_gamma_coding_lists(ordered_lists):
    return sum([_count_bytes_in_gamma_coding_list(ordered_list) for ordered_list in ordered_lists])


def analyze_posting_lists():
    logger = utils.get_default_logger()
    logger.addHandler(logging.FileHandler(filename="output/posting_lists_sizes.txt", mode="w"))
    logger.info("Creating posting lists with 128 coding...")
    postings_lists_128_coded = _create_terms_posting_lists(coding=128)
    logger.info("Creating posting lists with 16 coding...")
    postings_lists_16_coded = _create_terms_posting_lists(coding=16)
    ordered_lists = [posting_list.decode_to_ordered_list() for posting_list in postings_lists_128_coded]
    bytes_in_128_posting_lists = _count_bytes_in_postings_lists(postings_lists_128_coded)
    bytes_in_16_posting_lists = _count_bytes_in_postings_lists(postings_lists_16_coded)
    bytes_in_int32_lists = _count_int32_bytes_in_ordered_lists(ordered_lists)
    bytes_in_gamma_coding_lists = _count_bytes_in_gamma_coding_lists(ordered_lists)
    logger.info(f"Bytes in 128 coded posting lists: {bytes_in_128_posting_lists}")
    logger.info(f"Bytes in 16 coded posting lists: {bytes_in_16_posting_lists}")
    logger.info(f"Bytes in int32 lists: {bytes_in_int32_lists}")
    logger.info(f"Bytes in gamma coding lists: {bytes_in_gamma_coding_lists}")


if __name__ == "__main__":
    analyze_posting_lists()
