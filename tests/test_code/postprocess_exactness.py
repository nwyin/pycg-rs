"""Focused fixtures for exact postprocess behavior."""


class Parent:
    def ping(self):
        pass


class Child(Parent):
    def ping(self):
        pass


class Sibling:
    def ping(self):
        pass


def wildcard_ping_caller():
    ping()  # noqa: F821  # unresolved bare call expands during postprocess
