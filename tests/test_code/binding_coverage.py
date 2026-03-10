"""Test fixture exercising binding/assignment patterns.

Tests tuple/list unpacking, starred targets, attribute assignment,
and nested destructuring — all with distinct types so edge resolution
can be verified per-position.
"""


class X:
    def x_method(self):
        pass


class Y:
    def y_method(self):
        pass


class Z:
    def z_method(self):
        pass


def tuple_unpack():
    a, b = X(), Y()
    a.x_method()
    b.y_method()


def list_unpack():
    [a, b] = [X(), Y()]
    a.x_method()
    b.y_method()


def nested_tuple_unpack():
    (a, (b, c)) = (X(), (Y(), Z()))
    a.x_method()
    b.y_method()
    c.z_method()


def starred_unpack():
    a, *rest = X(), Y(), Z()
    a.x_method()


class Container:
    def __init__(self):
        self.item = X()

    def use_item(self):
        self.item.x_method()


def aug_assign():
    x = [X()]
    x += [Y()]
