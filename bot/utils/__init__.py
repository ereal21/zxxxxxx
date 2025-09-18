from decimal import Decimal, ROUND_HALF_UP

from .names import generate_internal_name, display_name


def format_amount(value) -> str:
    """Format numbers to a user-friendly monetary string."""
    decimal_value = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    text = format(decimal_value, 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text


__all__ = ['generate_internal_name', 'display_name', 'format_amount']
