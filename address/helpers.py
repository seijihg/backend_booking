import re

from django.core.exceptions import ValidationError


def validate_uk_postcode(postcode):
    if not postcode:  # Skip validation if the postcode is blank
        return

    pattern = r"([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9][A-Za-z]?))))\s?[0-9][A-Za-z]{2})"
    match = re.search(pattern, postcode)

    if not match:
        raise ValidationError("Invalid UK postcode.")
