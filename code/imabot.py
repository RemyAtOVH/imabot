#!/usr/bin/env python3
# -*- coding: utf8 -*-

import discord

from loguru import logger

# Log Internal imports
logger.info('Imports OK')

from variables import (
    DISCORD_GUILD,
    DISCORD_TOKEN,
)

# Log Internal imports
logger.info('Internal ENV vars loading OK')

try:
    if DISCORD_GUILD:
        bot = discord.Bot(debug_guilds=[DISCORD_GUILD])
    else:
        bot = discord.Bot()
except Exception as e:
    logger.error(f'Discord connection KO [{e}]')
else:
    logger.info('Discord connection OK')


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
