#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""🤖 Module to build Discord interactions and automate IT actions 🤖."""

import json

import discord
import tabulate
import ovh

from discord.commands import option
from discord.ext import commands
from loguru import logger
from tabulate import tabulate

from variables import (
    DISCORD_GUILD,
    DISCORD_TOKEN,
    OVH_AK,
    OVH_AS,
    OVH_CK,
    OVH_ENDPOINT,
    ROLE_TECH_RO,
    ROLE_TECH_RW,
)

from autocomplete import (
    get_project_list,
    get_user_list,
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
@commands.has_any_role(ROLE_TECH_RO)
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

@group_singouin.command(
    description='/ovh Commands related to OpenStack users',
    default_permission=False,
    name='user',
    )
@commands.has_any_role(ROLE_TECH_RO)
@option(
    "action",
    description="Users action",
    autocomplete=discord.utils.basic_autocomplete(
        [
            discord.OptionChoice("delete", value="delete"),
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
@option(
    "userid",
    description="User ID",
    autocomplete=get_user_list,
    required=False,
    )
async def user(
    ctx,
    action: str,
    projectid: str,
    userid: str,
):
    """
    This part performs actions on Public Cloud (OpenStack) users
    So far:
    - delete: Deletes a specific User
    - list: Displays the list of ALL Users
    - show: Displays the details of a specific User
    """
    # As we rely on potentially a lot of API calls, we need time to answer
    await ctx.defer()
    # Pre-flight checks
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(
        f'[#{channel}][{name}] /ovh user '
        f'{action} {projectid} {userid}'
        )

    if action == 'list':
        # We start with the headers
        embed_field_value_table = {
            'User Name': [],
            'User Desc.': [],
        }

        try:
            projects = ovh_client.get('/cloud/project')
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

            embed = discord.Embed(
                title=f'**{my_nic}**',
                colour=discord.Colour.green()
                )

            for project_id in projects:
                project = ovh_client.get(f'/cloud/project/{project_id}')

                if project['status'] == 'suspended':
                    # Suspended Projects cannot be queried later
                    embed.add_field(
                        name=f'Project ID: **{project_id}**',
                        value='(Suspended)',
                        inline=False,
                        )
                    continue

                users = ovh_client.get(f'/cloud/project/{project_id}/user')
                if len(users) == 0:
                    # There is no Users in the Project
                    embed.add_field(
                        name=f'Project ID: **{project_id}**',
                        value='No Users',
                        inline=False,
                        )
                    continue

                for user in users:
                    # We loop over the users to grab their names
                    embed_field_value_table['User Name'].append(user['username'])
                    embed_field_value_table['User Desc.'].append(user['description'])

                embed.add_field(
                    name=f'Project ID: **{project_id}**',
                    value=(
                        '```' +
                        tabulate(
                            embed_field_value_table,
                            headers='keys',
                            tablefmt='pretty',
                            stralign='right',
                            ) +
                        '```'
                        ),
                    inline=False,
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
        if projectid is None or userid is None:
            logger.error('Missing mandatory option(s)')
            msg = (
                'Check that you provided all variables: \n'
                ' - `projectid` \n'
                ' - `userid` \n'
                )
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            user = ovh_client.get(
                f'/cloud/project/{projectid}/user/{userid}'
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
            embed = discord.Embed(
                description=(
                    f'```json\n'
                    f'{json.dumps(user, indent=4)}'
                    f'\n```'
                    ),
                colour=discord.Colour.green()
            )
            await ctx.respond(embed=embed)

        logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        return
    elif action == 'delete':
        # Here for this one, we need more elevated role - TECH_RW
        # Pre-flight checks : Roles
        role_rw = discord.utils.get(ctx.author.guild.roles, name=ROLE_TECH_RW)
        if role_rw not in ctx.author.roles:
            msg = (
                f'[#{channel}][{name}]  └──> Missing required role (@{ROLE_TECH_RW})'
                )
            logger.warning(msg)
            embed = discord.Embed(
                description=(
                    f"You don't have the role requested for this operation (@{ROLE_TECH_RW})"
                    ),
                colour=discord.Colour.orange()
            )
            await ctx.respond(embed=embed)
            return

        if projectid is None or userid is None:
            logger.error('Missing mandatory option(s)')
            msg = (
                'Check that you provided all variables: \n'
                ' - `projectid` \n'
                ' - `userid` \n'
                )
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            user = ovh_client.get(
                f'/cloud/project/{projectid}/user/{userid}'
                )
            ovh_client.delete(
                f'/cloud/project/{projectid}/user/{userid}'
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
            embed = discord.Embed(
                title=f'**{my_nic}**',
                description=(
                    f"The Public Cloud (OpenStack) User "
                    f"`{user['username']}` ({user['description']}) "
                    f"was deleted"
                    ),
                colour=discord.Colour.green()
            )
            embed.set_footer(text=f"Project ID: {projectid}")

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
