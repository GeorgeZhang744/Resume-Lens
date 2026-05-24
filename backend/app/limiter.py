"""
Shared rate limiter instance.

Using slowapi (FastAPI equivalent of Flask-Limiter) with in-memory storage —
no Redis required for a single-instance deployment.

Limits are applied per client IP address.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
