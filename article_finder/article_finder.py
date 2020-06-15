import itertools
import time
from collections import defaultdict, Counter

import termcolor
from argparse import ArgumentParser
import re

import embeddings
import articles
import utils


def parse_input_arguments():
    parser = ArgumentParser()
    parser.add_argument("-show_similar_documents", type=bool, default=False)
    parser.add_argument("-embeddings_load_path", type=str, default=None)
    parser.add_argument("-embeddings_save_path", type=str, default=None)
    return parser.parse_args()


def get_word_trigrams(word):
    marked_word = f"${word}"
    trigrams = []
    for index in range(2, len(marked_word)):
        trigram = marked_word[index - 2: index + 1].lower()
        trigrams.append(trigram)
    return trigrams


def create_trigrams_article_ids(wiki_articles):
    trigrams_article_ids = defaultdict(lambda: set())
    for wiki_article in wiki_articles:
        for title_word in wiki_article.title.split(" "):
            for trigram in get_word_trigrams(title_word):
                trigrams_article_ids[trigram].add(wiki_article.id)
    return trigrams_article_ids


def get_words_lengths_penalty(query, title):
    words_of_query = query.split(" ")
    words_of_title = title.split(" ")
    if len(words_of_query) != words_of_title:
        return 0
    penalty = 0
    for word1, word2 in zip(words_of_query, words_of_title):
        penalty += abs(len(word1) - len(word2))
    return penalty


def get_words_count_penalty(query, title):
    return 3 * abs(len(query.split(" ")) - len(title.split(" ")))


def truncate_parentheses(text):
    while True:
        regex_match = re.search("(.*)\\((.*)\\)(.*)", text)
        if regex_match is None:
            return text
        text = f"{regex_match.group(1).strip()} {regex_match.group(3).strip()}".strip()


def create_article_ids_trigrams(query, trigrams_article_ids):
    trigrams_of_query = list(itertools.chain(*[get_word_trigrams(x) for x in query.split(" ")]))
    article_ids_trigrams_counter = Counter()
    for trigram in trigrams_of_query:
        for article_id in trigrams_article_ids[trigram]:
            article_ids_trigrams_counter[article_id] += 1
    return article_ids_trigrams_counter


def find_best_article_id_with_matching_ids(trigrams_article_ids, ids_wiki_articles, query):
    article_ids_trigrams_counter = create_article_ids_trigrams(query, trigrams_article_ids)
    article_ids_scores = {}
    chosen_article_ids_trigrams = sorted(article_ids_trigrams_counter.items(), key=lambda x: -x[1])[:100]
    for article_id, trigram_count in chosen_article_ids_trigrams:
        lengths_penalty = get_words_lengths_penalty(query, ids_wiki_articles[article_id].title)
        count_penalty = get_words_count_penalty(query, ids_wiki_articles[article_id].title)
        article_ids_scores[article_id] = article_ids_trigrams_counter[article_id] - lengths_penalty - count_penalty
    best_article_id = max(article_ids_scores.items(), key=lambda x: x[1])[0]
    best_title = ids_wiki_articles[best_article_id].title
    matching_article_ids = []
    for article_id, trigram_count in chosen_article_ids_trigrams:
        if truncate_parentheses(best_title) == truncate_parentheses(ids_wiki_articles[article_id].title):
            matching_article_ids.append(article_id)
    return best_article_id, matching_article_ids


def show_wiki_articles(wiki_articles):
    for wiki_article in wiki_articles:
        print(termcolor.colored(wiki_article.title, color="blue"))
        print(wiki_article.content)


def process_query(query, input_arguments, article_embeddings, ids_wiki_articles, trigrams_article_ids):
    start_time = time.time()
    best_id, matching_article_ids = find_best_article_id_with_matching_ids(
        trigrams_article_ids, ids_wiki_articles, query
    )
    print(termcolor.colored(f"Query: {query}", color="green"))
    if input_arguments.show_similar_documents:
        similar_article_ids = embeddings.get_close_embeddings_rows(best_id, article_embeddings)
        show_wiki_articles([ids_wiki_articles[x] for x in similar_article_ids])
    else:
        show_wiki_articles([ids_wiki_articles[x] for x in matching_article_ids])
    print(termcolor.colored(f"Answered in {time.time() - start_time} seconds", color="magenta"))
    print()


def get_article_embeddings(input_arguments, wiki_articles, logger):
    if not input_arguments.show_similar_documents:
        return None
    logger.info("Creating embeddings...")
    return embeddings.get_articles_embeddings(
        wiki_articles,
        input_arguments.embeddings_load_path,
        input_arguments.embeddings_save_path
    )


def run_article_finder(input_arguments):
    logger = utils.get_default_logger()
    logger.info("Reading wiki articles...")
    wiki_articles = articles.read_wiki_articles()
    article_embeddings = get_article_embeddings(input_arguments, wiki_articles, logger)
    logger.info("Creating n-grams...")
    ids_wiki_articles = {x.id: x for x in wiki_articles}
    trigrams_article_ids = create_trigrams_article_ids(wiki_articles)
    logger.info("All data prepared successfully...")
    while True:
        try:
            query = input().lower()
            process_query(query, input_arguments, article_embeddings, ids_wiki_articles, trigrams_article_ids)
        except EOFError:
            print("All input processed")
            break


if __name__ == "__main__":
    run_article_finder(parse_input_arguments())
