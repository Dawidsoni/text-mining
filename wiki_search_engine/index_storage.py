import sqlite3
import os
import json

from index_type import IndexType
from posting_list import PostingList
from wiki_article import WikiArticle


class IndexStorage(object):
    TRADITIONAL_INDEX_DATABASE_NAME = 'data/traditional_index.db'
    POSITIONAL_INDEX_DATABASE_NAME = 'data/positional_index.db'

    def __init__(self, index_type, truncate_old):
        self.database_name = IndexStorage._get_database_name(index_type)
        if truncate_old:
            self._truncate_old_if_exists()
        self.connection = sqlite3.connect(self.database_name)
        self.cursor = self.connection.cursor()
        self._create_tables_if_not_exists()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.commit_changes()
        self.connection.close()

    @staticmethod
    def _get_database_name(index_type):
        if index_type == IndexType.TRADITIONAL:
            return IndexStorage.TRADITIONAL_INDEX_DATABASE_NAME
        elif index_type == IndexType.POSITIONAL:
            return IndexStorage.POSITIONAL_INDEX_DATABASE_NAME
        elif index_type == IndexType.MIXED:
            return IndexStorage.TRADITIONAL_INDEX_DATABASE_NAME
        else:
            raise ValueError(f"Invalid index_type: {index_type}")
        
    def _truncate_old_if_exists(self):
        if os.path.exists(self.database_name):
            os.remove(self.database_name)

    def _create_tables_if_not_exists(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS indexed_terms
            (term TEXT PRIMARY KEY, posting_list BYTES)
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS wiki_articles
            (wiki_article_id BIGINT PRIMARY KEY, title TEXT, content TEXT)
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_base_forms
            (word TEXT PRIMARY KEY, base_forms TEXT)
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_positions
            (position INTEGER PRIMARY KEY)
        """)
        self.commit_changes()

    def add_indexed_term(self, term, posting_list):
        self.cursor.execute(
            "INSERT INTO indexed_terms (term, posting_list) VALUES (?, ?)",
            (term, posting_list.coded_sequence)
        )

    def add_wiki_article(self, wiki_article):
        self.cursor.execute(
            "INSERT INTO wiki_articles (wiki_article_id, title, content) VALUES (?, ?, ?)",
            (wiki_article.id, wiki_article.title, wiki_article.content)
        )

    def add_word_base_forms(self, word, base_forms):
        self.cursor.execute(
            "INSERT INTO word_base_forms (word, base_forms) VALUES (?, ?)",
            (word, json.dumps(base_forms))
        )

    def add_document_position(self, document_position):
        self.cursor.execute(
            "INSERT INTO document_positions (position) VALUES (?)",
            (document_position, )
        )

    def get_terms_postings_lists(self, terms):
        formatted_terms = ",".join(map(lambda term: f"'{term}'", terms))
        terms_postings_lists = self.cursor.execute(
            f"SELECT term, posting_list FROM indexed_terms WHERE term IN ({formatted_terms})"
        ).fetchall()
        return {x[0]: PostingList(x[1]) for x in terms_postings_lists}

    def get_wiki_articles(self, ids):
        formatted_ids = ",".join(map(lambda x: str(x), ids))
        articles_tuples = self.cursor.execute(
            f"SELECT wiki_article_id, title, content FROM wiki_articles WHERE wiki_article_id IN ({formatted_ids})"
        ).fetchall()
        return {x[0]: WikiArticle(id=x[0], title=x[1], content=x[2]) for x in articles_tuples}

    def get_words_base_forms(self, words):
        formatted_words = ",".join(map(lambda word: f"""'{word.replace("'", "")}'""", words))
        words_base_forms = self.cursor.execute(
            f"SELECT word, base_forms FROM word_base_forms WHERE word IN ({formatted_words})"
        ).fetchall()
        return {x[0]: json.loads(x[1]) for x in words_base_forms}

    def get_document_positions(self):
        fetched_data = self.cursor.execute("SELECT position FROM document_positions").fetchall()
        return [x[0] for x in fetched_data]

    def commit_changes(self):
        self.connection.commit()
