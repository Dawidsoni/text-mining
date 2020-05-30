from collections import defaultdict, Counter

import attr
import numpy as np
import scipy.sparse


@attr.s
class ArticleEmbeddings(object):
    normalized_embeddings = attr.ib()
    rows_ids = attr.ib()
    ids_rows = attr.ib()


def read_words_base_forms():
    words_base_forms = defaultdict(lambda: [])
    with open("data/base_forms.txt", "r") as file_stream:
        bases_words = map(lambda x: x.split(";")[0:2], file_stream.readlines())
        for base, word in bases_words:
            words_base_forms[word].append(base)
    return words_base_forms


def get_terms_indexes(words_base_forms, wiki_articles):
    terms_indexes = {}
    for wiki_article in wiki_articles:
        for word in wiki_article.content.split(" "):
            for base_form in words_base_forms[word.lower()]:
                if base_form not in terms_indexes:
                    terms_indexes[base_form] = len(terms_indexes)
    return terms_indexes


def create_tf_matrix(words_base_forms, wiki_articles, ids_rows, terms_indexes):
    tf_matrix = scipy.sparse.dok_matrix((len(ids_rows), len(terms_indexes)))
    for wiki_article in wiki_articles:
        article_terms_counter = Counter()
        for word in wiki_article.content.split(" "):
            for term in words_base_forms[word.lower()]:
                article_terms_counter[term] += 1
        sum_of_article_terms = sum(article_terms_counter.values())
        for term in article_terms_counter:
            value_for_term = article_terms_counter[term] / sum_of_article_terms
            tf_matrix[ids_rows[wiki_article.id], terms_indexes[term]] = value_for_term
    return tf_matrix


def create_idf_vector(words_base_forms, wiki_articles, terms_indexes):
    terms_documents_counts = Counter()
    for wiki_article in wiki_articles:
        article_terms = set()
        for word in wiki_article.content.split(" "):
            for term in words_base_forms[word.lower()]:
                if term in article_terms:
                    continue
                article_terms.add(term)
                terms_documents_counts[term] += 1
    idf_vector = np.zeros(shape=(len(terms_indexes), 1))
    for term, index_of_term in terms_indexes.items():
        idf_vector[index_of_term] = np.log2(len(wiki_articles) / terms_documents_counts[term])
    return idf_vector


def normalize_matrix(matrix):
    row_norms = np.sqrt(matrix.multiply(matrix).sum(axis=1)).reshape(-1, 1)
    return matrix.multiply(scipy.sparse.dok_matrix(1 / np.maximum(row_norms, 1e-3)))


def create_embeddings(wiki_articles, ids_rows):
    words_base_forms = read_words_base_forms()
    terms_indexes = get_terms_indexes(words_base_forms, wiki_articles)
    tf_matrix = create_tf_matrix(words_base_forms, wiki_articles, ids_rows, terms_indexes)
    idf_vector = create_idf_vector(words_base_forms, wiki_articles, terms_indexes).reshape(1, -1)
    tf_idf_matrix = tf_matrix.multiply(scipy.sparse.dok_matrix(idf_vector))
    return normalize_matrix(tf_idf_matrix)


def get_embeddings(wiki_articles, ids_rows, load_path=None):
    if load_path is not None:
        loaded_matrix = scipy.sparse.load_npz(load_path)
        return scipy.sparse.dok_matrix(loaded_matrix)
    return create_embeddings(wiki_articles, ids_rows)


def save_embeddings(embeddings, save_path):
    scipy.sparse.save_npz(save_path, scipy.sparse.csr_matrix(embeddings))


def get_rows_ids(wiki_articles):
    return dict(enumerate([x.id for x in sorted(wiki_articles, key=lambda x: x.id)]))


def get_articles_embeddings(wiki_articles, load_path=None, save_path=None):
    rows_ids = get_rows_ids(wiki_articles)
    ids_rows = dict([(y, x) for x, y in rows_ids.items()])
    embeddings = get_embeddings(wiki_articles, ids_rows, load_path)
    if save_path is not None:
        save_embeddings(embeddings, save_path)
    return ArticleEmbeddings(
        normalized_embeddings=embeddings,
        rows_ids=rows_ids,
        ids_rows=ids_rows
    )


def get_close_embeddings_rows(article_id, article_embeddings, count=10):
    row_id = article_embeddings.ids_rows[article_id]
    row_embedding = article_embeddings.normalized_embeddings.getrow(row_id).toarray().transpose()
    similarities = article_embeddings.normalized_embeddings.dot(row_embedding).reshape((-1, ))
    partition_index = len(similarities) - count - 1
    arg_partitioned_similarities = np.argpartition(similarities, kth=partition_index)
    selected_rows = arg_partitioned_similarities[partition_index:]
    selected_ids = [article_embeddings.rows_ids[x] for x in selected_rows]
    if article_id in selected_ids:
        selected_ids.remove(article_id)
    return list(reversed(selected_ids[:count]))
