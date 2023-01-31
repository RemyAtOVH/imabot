#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""🤖 Module to build Discord interactions and automate IT actions 🤖."""

import discord
import ovh

from loguru import logger

from variables import (
    DISCORD_GUILD,
    DISCORD_TOKEN,
    DISCORD_GROUP_ANSIBLE,
    DISCORD_GROUP_GENERAL,
    DISCORD_GROUP_PCI,
    DISCORD_GROUP_PCC,
    OVH_AK,
    OVH_AS,
    OVH_CK,
    OVH_ENDPOINT,
)

from subcommands import (
    ansible,
    general,
    public_cloud,
    private_cloud,
    )

# Log Internal imports
logger.info('Internal loading OK')

try:
    ovh_client = ovh.Client(
        endpoint=OVH_ENDPOINT,
        application_key=OVH_AK,
        application_secret=OVH_AS,
        consumer_key=OVH_CK,
        )
    me = ovh_client.get('/me')
    if me['nichandle']:
        my_nic = me['nichandle']

except Exception as e:
    logger.error(f'OVHcloud API connection KO [{e}]')
else:
    logger.info(f"OVHcloud API connection OK ({my_nic})")

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

# Additionnal error detector to answer properly
@bot.event
async def on_application_command_error(ctx, error):
    """Inform user of errors."""
    if isinstance(error, discord.ext.commands.NoPrivateMessage):
        await ctx.respond(
            "Sorry, this can't be done in DMs.",
            ephemeral=True
            )
    elif isinstance(error, discord.ext.commands.MissingPermissions):
        await ctx.respond(
            "Sorry, you don't have permission to do this.",
            ephemeral=True
            )
    elif isinstance(error, discord.ext.commands.CommandNotFound):
        await ctx.respond(
            "Sorry, unable to find the proper interaction.",
            ephemeral=True
            )
    elif isinstance(error, discord.ext.commands.MissingAnyRole):
        await ctx.respond(
            "Sorry, you are missing at least one of the required roles.",
            ephemeral=True
            )
    else:
        raise error

#
# /{DISCORD_GROUP_GENERAL} Slash Commands
#
try:
    group_global = bot.create_group(
        description="Commands related to Public Cloud requests",
        name=DISCORD_GROUP_GENERAL,
        )
except Exception as e:
    logger.error(f'Group KO (/{DISCORD_GROUP_GENERAL}) [{e}]')
else:
    logger.debug(f'Group OK (/{DISCORD_GROUP_GENERAL})')

general.billing(group_global, ovh_client, my_nic)
general.settings(group_global)


#
# /{DISCORD_GROUP_PCI} Slash Commands
#
try:
    group_pci = bot.create_group(
        description="Commands related to Public Cloud requests",
        name=DISCORD_GROUP_PCI,
        )
except Exception as e:
    logger.error(f'Group KO (/{DISCORD_GROUP_PCI}) [{e}]')
else:
    logger.debug(f'Group OK (/{DISCORD_GROUP_PCI})')

public_cloud.instance(group_pci, ovh_client, my_nic)
public_cloud.project(group_pci, ovh_client, my_nic)
public_cloud.user(group_pci, ovh_client, my_nic)
public_cloud.voucher(group_pci, ovh_client, my_nic)

#
# /{DISCORD_GROUP_PCC} Slash Commands
#
try:
    group_hpc = bot.create_group(
        description="Commands related to Hosted Private Cloud requests",
        name=DISCORD_GROUP_PCC,
        )
except Exception as e:
    logger.error(f'Group KO (/{DISCORD_GROUP_PCC}) [{e}]')
else:
    logger.debug(f'Group OK (/{DISCORD_GROUP_PCC})')

private_cloud.infrastructure(group_hpc, ovh_client, my_nic)
private_cloud.filer(group_hpc, ovh_client, my_nic)
private_cloud.user(group_hpc, ovh_client, my_nic)
private_cloud.vm(group_hpc, ovh_client, my_nic)


#
# /{DISCORD_GROUP_ANSIBLE} Slash Commands
#
try:
    group_ansible = bot.create_group(
        description="Commands related to Ansible actions",
        name=DISCORD_GROUP_ANSIBLE,
        )
except Exception as e:
    logger.error(f'Group KO (/{DISCORD_GROUP_ANSIBLE}) [{e}]')
else:
    logger.debug(f'Group OK (/{DISCORD_GROUP_ANSIBLE})')

ansible.hosts(group_ansible)
ansible.playbook(group_ansible)


#
# Run Discord bot
#
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    logger.error(f'Discord bot.run KO [{e}]')
