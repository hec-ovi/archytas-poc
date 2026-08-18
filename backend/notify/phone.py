"""Argentine mobile numbers for Meta's allow list.

Argentine mobiles carry a 9 between country code and area code (54 9 11 XXXX XXXX) and
that is the shape WhatsApp reports on inbound messages, so it is the shape we store. In
development mode the test number's allow list does an exact string match and refuses it
with 131030, so the 9 comes off at send time. Production has no allow list and takes
either form.
"""

from __future__ import annotations

AR_MOBILE_PREFIX = "549"


def to_wa_recipient(msisdn: str, development_mode: bool) -> str:
    """Number as Meta's `to` field wants it: digits only, no plus."""
    digits = msisdn.strip().lstrip("+").replace(" ", "").replace("-", "")
    if development_mode and digits.startswith(AR_MOBILE_PREFIX):
        return "54" + digits[len(AR_MOBILE_PREFIX) :]
    return digits
