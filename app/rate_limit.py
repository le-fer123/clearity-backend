"""
Rate limiting configuration for the application.
Separated from main.py to avoid circular imports.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance that can be imported by routes
limiter = Limiter(key_func=get_remote_address)
