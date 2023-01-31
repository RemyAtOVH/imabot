"""
Discord command definitions for /{DISCORD_GROUP_ANSIBLE} *
"""

from .hosts import hosts
from .playbook import playbook

__all__ = [
    'hosts',
    'playbook',
    ]
