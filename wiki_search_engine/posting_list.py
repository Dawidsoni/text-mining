from ordered_list import OrderedList


class PostingList(object):
    def __init__(self, coded_sequence=None, coding=128):
        self.coding = coding
        if coded_sequence is None:
            self.last_element = 0
            self.coded_sequence = bytearray()
        else:
            encoded_sequence = self.decode_from_bytes_to_list(coded_sequence)
            self.last_element = encoded_sequence[-1]
            self.coded_sequence = coded_sequence

    def _encode_value(self, value):
        if value <= 0:
            raise ValueError("Value to be encoded must be positive")
        coded_bytes = []
        while value > 0:
            coded_bytes.append(value % self.coding)
            value //= self.coding
        return coded_bytes[::-1]

    def _decode_value(self, bytes_list):
        encoded_value = 0
        for coded_byte in bytes_list:
            if coded_byte >= self.coding:
                raise ValueError(f"Coded byte cannot exceed value of self.coding, but was: {coded_byte}")
            encoded_value = encoded_value * self.coding + coded_byte
        return encoded_value

    def decode_from_bytes_to_list(self, coded_sequence):
        coded_value_bytes = []
        coded_value_increases = []
        for coded_byte in list(coded_sequence):
            coded_value_bytes.append(coded_byte % self.coding)
            if coded_byte >= self.coding:
                coded_value = self._decode_value(coded_value_bytes)
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
        coded_value_increase = self._encode_value(value_increase)
        coded_value_increase[-1] += self.coding
        self.coded_sequence += bytearray(coded_value_increase)
        self.last_element = document_id

    def append_if_not_equal_to_last_element(self, document_id):
        if self.last_element == document_id:
            return
        self.append(document_id)

    def decode_to_ordered_list(self):
        return OrderedList(self.decode_from_bytes_to_list(self.coded_sequence))
