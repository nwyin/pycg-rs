"""Test fixture exercising value resolution and attribute chains.

Covers chained attribute access, call-then-attribute, subscript resolution,
and MRO-based method lookup.
"""


class Inner:
    def deep_method(self):
        pass


class Outer:
    def __init__(self):
        self.inner = Inner()


class GrandParent:
    def inherited(self):
        pass


class MiddleParent(GrandParent):
    pass


class GrandChild(MiddleParent):
    pass


def chained_attr():
    o = Outer()
    o.inner.deep_method()


def call_then_attr():
    Outer().inner.deep_method()


def mro_grandchild():
    gc = GrandChild()
    gc.inherited()


def subscript_call():
    items = {"key": Inner()}
    items["key"].deep_method()
