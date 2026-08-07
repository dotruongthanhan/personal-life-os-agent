from datetime import timezone, timedelta

# This module holds shared application-wide context, like the user's timezone.
# It is initialized at startup in main.py.

# Default to UTC until it's properly initialized.
user_timezone = timezone(timedelta(0))