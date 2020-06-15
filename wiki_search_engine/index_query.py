import argparse
import functools
import itertools
import math
import re

import termcolor
from collections import defaultdict

import utils
from caching_index_storage import CachingIndexStorage
from index_type import IndexType
from posting_list import PostingList
from query import Query, QueryPart, QueryType
from search_result_rater import SearchResultRater


def _get_query_words_base_forms(index_storage, query):
    query_words = query.split(" ")
    words_base_forms = index_storage.get_words_base_forms(query_words)
    return [
        (word, words_base_forms[word]) if len(words_base_forms[word]) > 0 else (word, [word])
        for word in query_words
    ]


def get_words_terms_identifiers(words_base_forms, terms_identifiers):
    return {
        term: [terms_identifiers[base_form] for base_form in base_forms]
        for term, base_forms in words_base_forms.items()
    }


def _get_traditional_index_documents_ids(index_storage, query_words_base_forms, terms_identifiers):
    query_terms_identifiers = get_words_terms_identifiers(dict(query_words_base_forms), terms_identifiers)
    query_identifiers = set(itertools.chain(*query_terms_identifiers.values()))
    terms_identifiers_posting_lists = defaultdict(
        lambda: PostingList(), index_storage.get_terms_postings_lists(tuple(query_identifiers))
    )
    words_ordered_lists = set()
    for word, identifiers in query_terms_identifiers.items():
        word_ordered_lists = [terms_identifiers_posting_lists[x].decode_to_ordered_list() for x in identifiers]
        if len(word_ordered_lists) == 0:
            continue
        word_merged_ordered_list = functools.reduce(lambda x, y: x | y, word_ordered_lists)
        words_ordered_lists.add(word_merged_ordered_list)
    if len(words_ordered_lists) == 0:
        return ()
    return set(functools.reduce(lambda x, y: x & y, words_ordered_lists).items)


def _get_document_id_from_positions(documents_ids, term_position):
    start_index = 0
    end_index = len(documents_ids)
    while start_index < end_index:
        middle_index = math.ceil((start_index + end_index) / 2)
        if documents_ids[middle_index] > term_position:
            end_index = middle_index - 1
        elif documents_ids[middle_index] < term_position:
            start_index = middle_index
        else:
            return middle_index
    return start_index


def _get_positional_index_documents_ids(index_storage, query_words_base_forms, terms_identifiers):
    query_terms_identifiers = get_words_terms_identifiers(dict(query_words_base_forms), terms_identifiers)
    query_identifiers = set(itertools.chain(*query_terms_identifiers.values()))
    terms_identifiers_posting_lists = defaultdict(
        lambda: PostingList(), index_storage.get_terms_postings_lists(tuple(query_identifiers))
    )
    documents_ids = index_storage.get_document_positions()
    word_position = 0
    list_of_matched_positions = []
    for word, identifiers in query_terms_identifiers.items():
        list_of_word_positions = [terms_identifiers_posting_lists[x].decode_to_ordered_list() for x in identifiers]
        shifted_word_positions = {position - word_position for position in itertools.chain(*list_of_word_positions)}
        list_of_matched_positions.append(shifted_word_positions)
        word_position += 1
    matched_positions = functools.reduce(lambda x, y: x & y, list_of_matched_positions)
    return set([_get_document_id_from_positions(documents_ids, x) + 1 for x in matched_positions])


def _get_mixed_index_documents_ids(traditional_index_storage, positional_index_storage, query_parts,
                                   query_words_base_forms, terms_identifiers):
    if len(query_parts) == 0:
        return
    list_of_documents_ids = []
    for query_part in query_parts:
        query_words = set(query_part.raw_query.split(" "))
        words_base_forms_part = [
            words_base_forms for words_base_forms in query_words_base_forms
            if words_base_forms[0] in query_words
        ]
        if query_part.query_type == QueryType.NORMAL:
            list_of_documents_ids.append(_get_traditional_index_documents_ids(
                traditional_index_storage, words_base_forms_part, terms_identifiers
            ))
        elif query_part.query_type == QueryType.PHRASE:
            list_of_documents_ids.append(_get_positional_index_documents_ids(
                positional_index_storage, words_base_forms_part, terms_identifiers
            ))
        else:
            raise ValueError(f"Invalid query_type: {query_part.query_type}")
    return functools.reduce(lambda x, y: x & y, list_of_documents_ids)


def _get_matching_documents_ids(query, index_type, traditional_index_storage, positional_index_storage,
                                query_words_base_forms, terms_identifiers):
    if index_type == IndexType.TRADITIONAL:
        return _get_traditional_index_documents_ids(
            traditional_index_storage, query_words_base_forms, terms_identifiers
        )
    elif index_type == IndexType.POSITIONAL:
        return _get_positional_index_documents_ids(
            positional_index_storage, query_words_base_forms, terms_identifiers
        )
    elif index_type == IndexType.MIXED:
        return _get_mixed_index_documents_ids(
            traditional_index_storage, positional_index_storage, query.query_parts, query_words_base_forms,
            terms_identifiers
        )
    else:
        raise ValueError(f"Invalid index_type: {index_type}")


def _show_search_results(wiki_articles, index_storage, terms_identifiers, query_terms_identifiers, max_results):
    matching_identifiers = set(itertools.chain(*query_terms_identifiers.values()))
    for wiki_article in wiki_articles[:max_results]:
        print(termcolor.colored(wiki_article.title, color="green"))
        content_words = list(map(lambda x: x.lower(), wiki_article.content.split(" ")))
        content_words_base_forms = index_storage.get_words_base_forms(content_words)
        displayed_words_indexes = set()
        colored_words_indexes = set()
        for i in range(len(content_words)):
            word_base_forms = content_words_base_forms[content_words[i]]
            if len(word_base_forms) == 0:
                word_base_forms.append(content_words[i])
            word_identifiers = {terms_identifiers[base_form] for base_form in word_base_forms}
            if any([word_identifier in matching_identifiers for word_identifier in word_identifiers]):
                colored_words_indexes.add(i)
                displayed_words_indexes.update(range(i - 5, i + 6))
        for i in range(len(content_words)):
            if i in colored_words_indexes:
                print(termcolor.colored(content_words[i], color="blue"), end=" ")
            elif i in displayed_words_indexes:
                print(content_words[i], end=" ")
            elif i >= 1 and (i - 1) in displayed_words_indexes and i not in displayed_words_indexes:
                print()
        print("\n\n")


def _parse_input_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-index_type", type=IndexType, choices=list(IndexType.__dict__.values()))
    parser.add_argument("--use_terms_clusters", type=bool, default=False)
    return vars(parser.parse_args())


def _get_query(index_type):
    raw_query = input().lower()
    if index_type != IndexType.MIXED:
        return Query(raw_query, query_parts=[])
    parsed_query = raw_query
    query_parts = []
    while True:
        regex_match = re.search('(.*?)"(.*?)"(.*)', parsed_query)
        if regex_match is None:
            break
        parsed_query = f"{regex_match.group(1).strip()} {regex_match.group(3).strip()}"
        query_parts.append(QueryPart(regex_match.group(2), QueryType.PHRASE))
    if len(parsed_query.strip()) > 0:
        query_parts.append(QueryPart(parsed_query, QueryType.NORMAL))
    cleaned_query = raw_query.replace('"', '')
    return Query(cleaned_query, query_parts)


def run_index_query(index_type, use_terms_clusters):
    traditional_index_storage = CachingIndexStorage(IndexType.TRADITIONAL, use_terms_clusters, truncate_old=False)
    positional_index_storage = CachingIndexStorage(IndexType.POSITIONAL, use_terms_clusters, truncate_old=False)
    terms_identifiers = utils.get_terms_identifiers(use_terms_clusters)
    while True:
        print("Type query:")
        query = _get_query(index_type)
        query_words_base_forms = _get_query_words_base_forms(traditional_index_storage, query.raw_query)
        query_terms_identifiers = get_words_terms_identifiers(dict(query_words_base_forms), terms_identifiers)
        document_ids = _get_matching_documents_ids(
            query, index_type, traditional_index_storage, positional_index_storage, query_words_base_forms,
            terms_identifiers
        )
        wiki_articles = list(traditional_index_storage.get_wiki_articles(document_ids).values())
        search_result_rater = SearchResultRater(traditional_index_storage, query_words_base_forms)
        ranked_wiki_articles = list(sorted(wiki_articles, key=search_result_rater.rate_wiki_article, reverse=True))
        _show_search_results(
            ranked_wiki_articles, traditional_index_storage, terms_identifiers, query_terms_identifiers, max_results=10
        )


if __name__ == "__main__":
    run_index_query(**_parse_input_arguments())
