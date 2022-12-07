#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""Module to build Discord interactions (from pip:py-cord)."""
import discord
import ovh

from loguru import logger

from variables import (
    DISCORD_GUILD,
    DISCORD_TOKEN,
    OVH_AK,
    OVH_AS,
    OVH_CK,
    OVH_ENDPOINT,
)

# Log Internal imports
logger.info('Internal loading OK')

try:
    if DISCORD_GUILD:
        bot = discord.Bot(debug_guilds=[DISCORD_GUILD])
    else:
        bot = discord.Bot()
except Exception as e:
    logger.error(f'Discord connection KO [{e}]')
else:
    logger.info('Discord connection OK')

try:
    ovhClient = ovh.Client(
        endpoint=OVH_ENDPOINT,
        application_key=OVH_AK,
        application_secret=OVH_AS,
        consumer_key=OVH_CK,
        )
    me = ovhClient.get('/me')
except Exception as e:
    logger.error(f'OVHcloud API connection KO [{e}]')
else:
    if me['nichandle']:
        logger.info(f"OVHcloud API connection OK ({me['nichandle']})")

@bot.event
async def on_ready():
    """Logs when bot connection to Discord is established."""
    logger.info(f'Discord on_ready OK ({bot.user})')


#
# Run Discord bot
#
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    logger.error(f'Discord bot.run KO [{e}]')
