#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""🤖 Module to build Discord interactions and automate IT actions 🤖."""

import json

import discord
import tabulate
import ovh

from discord.commands import option
from loguru import logger
from tabulate import tabulate

from variables import (
    DISCORD_GUILD,
    DISCORD_TOKEN,
    OVH_AK,
    OVH_AS,
    OVH_CK,
    OVH_ENDPOINT,
)

from autocomplete import (
    get_project_list,
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
    ovh_client = ovh.Client(
        endpoint=OVH_ENDPOINT,
        application_key=OVH_AK,
        application_secret=OVH_AS,
        consumer_key=OVH_CK,
        )
    me = ovh_client.get('/me')
    logger.error(me)
    if me['nichandle']:
        my_nic = me['nichandle']

except Exception as e:
    logger.error(f'OVHcloud API connection KO [{e}]')
else:
    logger.info(f"OVHcloud API connection OK ({my_nic})")

@bot.event
async def on_ready():
    """Logs when bot connection to Discord is established."""
    logger.info(f'Discord on_ready OK ({bot.user})')


#
# /ovh Slash Commands
#
try:
    group_singouin = bot.create_group(
        description="Commands related to OVHcloud",
        name='ovh',
        )
except Exception as e:
    logger.error(f'Group KO (/ovh) [{e}]')
else:
    logger.debug('Group OK (/ovh)')

@group_singouin.command(
    description='Display Public Cloud Project informations',
    default_permission=False,
    name='project',
    )
@option(
    "action",
    description="Project action",
    autocomplete=discord.utils.basic_autocomplete(
        [
            discord.OptionChoice("list", value="list"),
            discord.OptionChoice("show", value="show"),
            ]
        )
    )
@option(
    "projectid",
    description="Project ID",
    autocomplete=get_project_list,
    required=False,
    )
async def project(
    ctx,
    action: str,
    projectid: str,
):
    """
    This part performs actions on Public Cloud (OpenStack) projects
    So far:
    - list: Display the list of ALL Public Cloud projects
    - show: When provided a Project ID, will show its details
    """
    # As we rely on potentially a lot of API calls, we need time to answer
    await ctx.defer()
    # Pre-flight checks
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(f'[#{channel}][{name}] /ovh project {projectid}')

    if action == 'list':
        # We start with the headers
        projects_table = {
            'Nichandle': [],
            'Project ID': [],
            'Project Name': [],
            'Status': [],
        }

        try:
            myprojects = ovh_client.get('/cloud/project')
        except Exception as e:
            msg = f'API calls KO [{e}]'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        # We loop over the projects
        try:
            for project_id in myprojects:
                # We increment results counter
                myproject = ovh_client.get(f'/cloud/project/{project_id}')

                # Everything went well
                projects_table['Nichandle'].append(my_nic)
                projects_table['Project ID'].append(f'{project_id:.10}..')
                projects_table['Project Name'].append(f"{myproject['description']:>22}")
                projects_table['Status'].append(myproject['status'])

                embed = discord.Embed(
                    description=(
                        '```' +
                        tabulate(projects_table, headers='keys', tablefmt='pretty') +
                        '```'
                        ),
                    colour=discord.Colour.green()
                )
                await ctx.interaction.edit_original_response(
                    embed=embed
                    )
        except Exception as e:
            msg = f'API calls KO [{e}]'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return
        else:
            logger.debug(f'[#{channel}][{name}] └──> Queries OK')
            return
    elif action == 'show':
        if projectid:
            pass
        else:
            msg = 'Variable not given: `projectid`'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            project_response = ovh_client.get(f'/cloud/project/{projectid}')
        except Exception as e:
            msg = f'API calls KO [{e}]'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return
        else:
            embed = discord.Embed(
                description=(
                    f'```json\n'
                    f'{json.dumps(project_response, indent=4)}'
                    f'\n```'
                    ),
                colour=discord.Colour.green()
            )
            await ctx.respond(embed=embed)

        logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        return

#
# Run Discord bot
#
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    logger.error(f'Discord bot.run KO [{e}]')
