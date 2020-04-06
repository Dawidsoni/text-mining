class OrderedList(object):
    def __init__(self, items):
        self.items = tuple(items)
        OrderedList._assert_ordered(self.items)

    @staticmethod
    def _assert_ordered(items):
        for i in range(1, len(items)):
            if items[i - 1] > items[i]:
                raise ValueError("Cannot initialize OrderedList with unsorted items")

    def __and__(self, other):
        items_intersection = []
        self_index, other_index = 0, 0
        while self_index < len(self.items) and other_index < len(other.items):
            if self.items[self_index] < other.items[other_index]:
                self_index += 1
            elif self.items[self_index] > other.items[other_index]:
                other_index += 1
            else:
                items_intersection.append(self.items[self_index])
                self_index += 1
                other_index += 1
        return OrderedList(items_intersection)

    def __or__(self, other):
        items_union = []
        self_index, other_index = 0, 0
        while self_index < len(self.items) or other_index < len(other.items):
            if other_index == len(other.items):
                items_union.append(self.items[self_index])
                self_index += 1
            elif self_index == len(self.items):
                items_union.append(other.items[other_index])
                other_index += 1
            elif self.items[self_index] < other.items[other_index]:
                items_union.append(self.items[self_index])
                self_index += 1
            elif self.items[self_index] > other.items[other_index]:
                items_union.append(other.items[other_index])
                other_index += 1
            else:
                items_union.append(self.items[self_index])
                self_index += 1
                other_index += 1
        return OrderedList(items_union)
