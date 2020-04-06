import functools
import attr
from index_storage import IndexStorage
from posting_list import PostingList


@attr.s()
class ListItemCache(object):
    item = attr.ib()
    value = attr.ib(default=None)


class CachingIndexStorage(IndexStorage):

    def __init__(self, truncate_old):
        super().__init__(truncate_old)

    @functools.lru_cache(maxsize=10_000_000)
    def _list_items_cache(self, _func, item):
        return ListItemCache(item=item)

    @staticmethod
    def _resolve_items(items_caches, resolve_func, default_value=None):
        unresolved_items_caches = list(filter(lambda x: x.value is None, items_caches))
        if len(unresolved_items_caches) == 0:
            return
        items_values = resolve_func(list(map(lambda x: x.item, unresolved_items_caches)))
        for item_cache in unresolved_items_caches:
            if item_cache.item in items_values:
                item_cache.value = items_values[item_cache.item]
            elif default_value is not None:
                item_cache.value = default_value
            else:
                raise ValueError(f"Cannot resolve item: {item_cache.item}")

    def get_terms_postings_lists(self, terms):
        items_caches = [self._list_items_cache(self.get_terms_postings_lists, x) for x in terms]
        CachingIndexStorage._resolve_items(items_caches, super().get_terms_postings_lists, default_value=PostingList())
        return {x.item: x.value for x in items_caches}

    def get_wiki_articles(self, ids):
        items_caches = [self._list_items_cache(self.get_wiki_articles, x) for x in ids]
        CachingIndexStorage._resolve_items(items_caches, super().get_wiki_articles)
        return {x.item: x.value for x in items_caches}

    def get_words_base_forms(self, words):
        items_caches = [self._list_items_cache(self.get_words_base_forms, x) for x in words]
        CachingIndexStorage._resolve_items(items_caches, super().get_words_base_forms, default_value=[])
        return {x.item: x.value for x in items_caches}
