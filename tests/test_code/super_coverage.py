"""Focused coverage for super() resolution."""


class Base:
    def greet(self):
        pass


class Derived(Base):
    def greet(self):
        super().greet()
