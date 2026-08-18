"""Closed error set for the normalizer box."""


class NormalizerError(Exception):
    """Base for everything this box raises."""


class UnknownCatalog(NormalizerError):
    """A matcher was asked to resolve against a catalog that was never loaded."""
