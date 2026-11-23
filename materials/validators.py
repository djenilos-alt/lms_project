from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_youtube_url(value):
    """Разрешает ссылки только на youtube.com и его поддомены."""
    parsed_url = urlparse(value)
    hostname = parsed_url.hostname

    if not hostname or not (
        hostname == "youtube.com"
        or hostname.endswith(".youtube.com")
    ):
        raise ValidationError(
            "Разрешены только ссылки на YouTube (youtube.com)."
        )
