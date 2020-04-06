import functools
import itertools
import termcolor
from collections import defaultdict

from caching_index_storage import CachingIndexStorage
from posting_list import PostingList
from search_result_rater import SearchResultRater


def _get_query_words_base_forms(index_storage, query):
    query_words = query.split(" ")
    words_base_forms = index_storage.get_words_base_forms(query_words)
    return {
        x: words_base_forms[x] if len(words_base_forms[x]) > 0 else [x]
        for x in words_base_forms.keys()
    }


def _get_matching_documents_ids(query_words_base_forms, base_forms_posting_lists):
    words_ordered_lists = set()
    for word, base_forms in query_words_base_forms.items():
        word_ordered_lists = list(map(lambda x: base_forms_posting_lists[x].decode_to_ordered_list(), base_forms))
        if len(word_ordered_lists) == 0:
            continue
        word_merged_ordered_list = functools.reduce(lambda x, y: x | y, word_ordered_lists)
        words_ordered_lists.add(word_merged_ordered_list)
    if len(words_ordered_lists) == 0:
        return ()
    return functools.reduce(lambda x, y: x & y, words_ordered_lists).items


def _show_search_results(wiki_articles, index_storage, query_base_forms, max_results):
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
            if any([word_base_form in query_base_forms for word_base_form in word_base_forms]):
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


def run_index_query():
    index_storage = CachingIndexStorage(truncate_old=False)
    while True:
        print("Type query:")
        query = input().lower()
        query_words_base_forms = _get_query_words_base_forms(index_storage, query)
        query_base_forms = set(itertools.chain(*query_words_base_forms.values()))
        base_forms_posting_lists = defaultdict(
            lambda: PostingList(), index_storage.get_terms_postings_lists(tuple(query_base_forms))
        )
        document_ids = _get_matching_documents_ids(query_words_base_forms, base_forms_posting_lists)
        wiki_articles = list(index_storage.get_wiki_articles(document_ids).values())
        search_result_rater = SearchResultRater(index_storage, query_words_base_forms)
        ranked_wiki_articles = list(sorted(wiki_articles, key=search_result_rater.rate_wiki_article, reverse=True))
        _show_search_results(ranked_wiki_articles, index_storage, query_base_forms, max_results=10)


if __name__ == "__main__":
    run_index_query()
