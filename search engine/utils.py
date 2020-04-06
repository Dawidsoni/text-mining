from collections import defaultdict


def read_words_base_forms():
    words_base_forms = defaultdict(lambda: [])
    with open("base_forms.txt", "r") as file_stream:
        bases_words = map(lambda x: x.split(";")[0:2], file_stream.readlines())
        for base, word in bases_words:
            words_base_forms[word].append(base)
    return dict(words_base_forms)


def read_quotes():
    with open("tokenized_quotes.txt", "r") as file_stream:
        return list(map(lambda x: x.strip(), file_stream.readlines()))


def read_trigrams():
    with open("trigrams.txt", "r") as file_stream:
        return list(map(lambda x: x.strip(), file_stream.readlines()))
