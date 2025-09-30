"""
singleton.py — Singleton Decorator

A decorator-based (not metaclass-based) singleton implementation.
Apply @Singleton to any class whose constructor takes only `self`, then
access the single shared instance via `YourClass.instance()`.
"""


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a decorator.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the decorator instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the decorator instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
