# -*- coding: utf8 -*-

"""Module to get ENV vars."""
import os

# Discord credentials
DISCORD_GUILD = os.environ.get("DISCORD_GUILD", None)
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# OVHcloud API credentials
"""
You can generate them here: https://api.ovh.com/createToken/
DO NOT HARDCODE THEM HERE !
They are meant to be passed as ENV vars (secrets) to ensure your safety.
"""
OVH_ENDPOINT = os.environ.get("OVH_ENDPOINT", 'ovh-eu')
OVH_AK = os.environ.get("OVH_APPLICATION_KEY")
OVH_AS = os.environ.get("OVH_APPLICATION_SECRET")
OVH_CK = os.environ.get("OVH_CONSUMER_KEY")
