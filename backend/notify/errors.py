"""Closed error set for the notify box.

A message that could not be delivered is not an error: it comes back as a failed
Delivery. Only a broken configuration raises.
"""


class NotifyError(Exception):
    """Base for everything this box raises."""


class UnknownChannel(NotifyError):
    """NOTIFY_CHANNELS names a channel this box does not implement."""
