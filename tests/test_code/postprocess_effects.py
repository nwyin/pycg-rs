"""Test fixture for postprocessing effects.

Exercises cull_inherited, collapse_inner, and contract_nonexistents
in ways where their deletion produces observable edge differences.
"""


class Parent:
    def inherited_method(self):
        pass

    def parent_only(self):
        pass


class Child(Parent):
    def own_method(self):
        pass


def caller_uses_child():
    """After cull_inherited, edge should go to Child (or Parent), not both."""
    c = Child()
    c.inherited_method()
    c.own_method()


def caller_with_lambda():
    """After collapse_inner, lambda's edges merge into this function."""
    fn = lambda: Child().own_method()
    fn()


def caller_with_listcomp():
    """After collapse_inner, comprehension edges merge into this function."""
    result = [Child() for _ in range(1)]
    return result
