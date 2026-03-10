"""Fixture where only expand_unknowns can add concrete targets."""


class WorkerA:
    def do_work(self):
        pass


class WorkerB:
    def do_work(self):
        pass


def wildcard_only():
    do_work()  # noqa: F821  # intentionally unresolved
