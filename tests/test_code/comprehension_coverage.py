"""Focused coverage for set/dict/generator comprehensions."""


class Sequence:
    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration


def set_comp_protocol():
    seq = Sequence()
    return {item for item in seq}


def dict_comp_protocol():
    seq = Sequence()
    return {item: item for item in seq}


def genexpr_protocol():
    seq = Sequence()
    return (item for item in seq)
