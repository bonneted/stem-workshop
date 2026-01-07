# Ref: https://docs.gunicorn.org/en/stable/settings.html#config-file
#
import os

bind = f"{os.environ.get('SERVER_LISTEN_IP', '0.0.0.0')}:{os.environ.get('PORT', '8050')}"
errorlog = "-"  # pylint: disable=invalid-name
loglevel = os.environ.get("LOGGER_LEVEL", "info")

