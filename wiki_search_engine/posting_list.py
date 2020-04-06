from ordered_list import OrderedList


class PostingList(object):
    def __init__(self, coded_sequence=None):
        if coded_sequence is None:
            self.last_element = 0
            self.coded_sequence = bytearray()
        else:
            encoded_sequence = PostingList.decode_from_bytes_to_list(coded_sequence)
            self.last_element = encoded_sequence[-1]
            self.coded_sequence = coded_sequence

    @staticmethod
    def _to_128_coding(value):
        if value <= 0:
            raise ValueError("Value to be encoded must be positive")
        coded_bytes = []
        while value > 0:
            coded_bytes.append(value % 128)
            value //= 128
        return coded_bytes[::-1]

    @staticmethod
    def _from_128_coding(bytes_list):
        encoded_value = 0
        for coded_byte in bytes_list:
            if coded_byte >= 128:
                raise ValueError(f"Coded byte cannot exceed value of 128, but was: {coded_byte}")
            encoded_value = encoded_value * 128 + coded_byte
        return encoded_value

    @staticmethod
    def decode_from_bytes_to_list(coded_sequence):
        coded_value_bytes = []
        coded_value_increases = []
        for coded_byte in list(coded_sequence):
            coded_value_bytes.append(coded_byte % 128)
            if coded_byte >= 128:
                coded_value = PostingList._from_128_coding(coded_value_bytes)
                coded_value_increases.append(coded_value)
                coded_value_bytes = []
        coded_values = []
        for value_increase in coded_value_increases:
            last_value = coded_values[-1] if len(coded_values) > 0 else 0
            coded_values.append(last_value + value_increase)
        return coded_values

    def append(self, document_id):
        if document_id <= self.last_element:
            raise ValueError(f"Added document ID can't be less than the last document ID")
        value_increase = document_id - self.last_element
        coded_value_increase = PostingList._to_128_coding(value_increase)
        coded_value_increase[-1] += 128
        self.coded_sequence += bytearray(coded_value_increase)
        self.last_element = document_id

    def decode_to_ordered_list(self):
        return OrderedList(PostingList.decode_from_bytes_to_list(self.coded_sequence))
