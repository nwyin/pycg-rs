"""Test fixture for relative import resolution at various levels."""

from . import sibling  # noqa: F401  — level=1, module=sibling
from .sibling import sibling_func  # noqa: F401  — level=1, item import
from .deep.inner import deep_func  # noqa: F401  — level=1, nested package


def caller():
    sibling_func()
    deep_func()
