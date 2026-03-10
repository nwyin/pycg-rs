"""Test fixture exercising statement types that need observable edges.

Each function uses a distinct construct (while, try, match, augmented assign,
annotated assign, lambda, default args) that produces a call edge to Worker.process.
"""


class Worker:
    def process(self):
        pass


class Helper:
    def assist(self):
        pass


def uses_while():
    w = Worker()
    while True:
        w.process()
        break


def uses_try():
    w = Worker()
    try:
        w.process()
    except Exception:
        pass


def uses_try_except_body():
    h = Helper()
    try:
        pass
    except Exception:
        h.assist()


def uses_match(cmd):
    w = Worker()
    match cmd:
        case "go":
            w.process()
        case _:
            pass


def uses_ann_assign():
    x: Worker = Worker()
    x.process()


def uses_lambda():
    fn = lambda: Worker().process()
    fn()


def uses_defaults(x=Worker()):
    x.process()


# For loop target binding
def uses_for():
    items = [Worker()]
    for w in items:
        w.process()


# With statement
def uses_with():
    w = Worker()
    with w:
        w.process()


# Global / nonlocal (scope defs must collect these)
_global_var = None


def uses_global():
    global _global_var
    _global_var = Worker()


def outer():
    captured = None

    def inner():
        nonlocal captured
        captured = Worker()

    inner()
