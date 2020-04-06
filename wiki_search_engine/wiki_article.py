import attr


@attr.s(frozen=True)
class WikiArticle(object):
    id = attr.ib()
    title = attr.ib()
    content = attr.ib()
