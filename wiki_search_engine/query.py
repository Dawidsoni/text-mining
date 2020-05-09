from enum import Enum

import attr


class QueryType(Enum):
    NORMAL = "NORMAL"
    PHRASE = "PHRASE"


@attr.s
class QueryPart(object):
    raw_query = attr.ib()
    query_type = attr.ib()


@attr.s
class Query(object):
    raw_query = attr.ib()
    query_parts = attr.ib()