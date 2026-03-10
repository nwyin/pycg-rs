"""Fixture that requires more than one propagation pass."""


def consumer():
    outer().make()


def outer():
    return middle()


def middle():
    return inner()


def inner():
    return Product()


class Product:
    def make(self):
        pass
