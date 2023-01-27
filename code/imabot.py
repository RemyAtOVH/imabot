#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""🤖 Module to build Discord interactions and automate IT actions 🤖."""

import json
import re
import textwrap

import discord
import tabulate
import ovh

from discord.commands import option
from discord.ext import commands
from loguru import logger
from tabulate import tabulate

from subcommands import general

from variables import (
    DISCORD_GUILD,
    DISCORD_TOKEN,
    DISCORD_GROUP_GENERAL,
    DISCORD_GROUP_PCI,
    DISCORD_GROUP_PCC,
    OVH_AK,
    OVH_AS,
    OVH_CK,
    OVH_ENDPOINT,
    ROLE_TECH_RO,
    ROLE_TECH_RW,
    ROLE_ACCOUNTING,
)

from autocomplete import (
    get_hpc_list,
    get_hpc_filer_list,
    get_hpc_user_list,
    get_instance_list,
    get_project_list,
    get_sshkey_list,
    get_user_list,
    get_voucher_list,
)
from views import InstanceCreationView

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

@group_pci.command(
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
    # Pre-flight checks: Channel
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(f'[#{channel}][{name}] /{DISCORD_GROUP_PCI} project {projectid}')

    if action == 'list':
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
            embed = discord.Embed(
                title=f'**{my_nic}**',
                colour=discord.Colour.green()
                )

            for project_id in myprojects:
                # We start with the headers
                embed_field_value_table = {
                    'Project Name': [],
                    'Project Status': [],
                }

                project = ovh_client.get(f'/cloud/project/{project_id}')

                if project['status'] == 'suspended':
                    # Suspended Projects cannot be queried later
                    embed.add_field(
                        name=f'Project ID: **{project_id}**',
                        value='(Suspended)',
                        inline=False,
                        )
                    continue

                # Everything went well
                embed_field_value_table['Project Name'].append(project['description'])
                embed_field_value_table['Project Status'].append(project['status'])

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

@group_pci.command(
    description='Commands related to OpenStack users',
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
    # Pre-flight checks: Channel
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(
        f'[#{channel}][{name}] /{DISCORD_GROUP_PCI} user '
        f'{action} {projectid} {userid}'
        )

    if action == 'list':
        # This command will require basic TECH_RO role, checked before
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
                # We start with the headers
                embed_field_value_table = {
                    'User Name': [],
                    'User Desc.': [],
                    }

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
        # This command will require basic TECH_RO role, checked before
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

@group_pci.command(
    description='Commands related to Project Vouchers',
    default_permission=False,
    name='voucher',
    )
@commands.has_any_role(ROLE_ACCOUNTING)
@option(
    "action",
    description="Voucher action",
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
@option(
    "voucherid",
    description="Voucher ID",
    autocomplete=get_voucher_list,
    required=False,
    )
async def voucher(
    ctx,
    action: str,
    projectid: str,
    voucherid: str,
):
    """
    This part performs actions on Public Cloud vouchers
    So far:
    - list: Displays the list of ALL Vouchers
    - show: Displays the details of a specific Voucher
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
        f'[#{channel}][{name}] /{DISCORD_GROUP_PCI} voucher '
        f'{action} {projectid} {voucherid}'
        )

    if action == 'list':
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
                # We start with the headers
                embed_field_value_table = {
                    'Voucher': [],
                    'Avail.': [],
                    'Used': [],
                    'Description': [],
                    }

                credits_id = ovh_client.get(f'/cloud/project/{project_id}/credit')
                if len(credits_id) == 0:
                    # There is no Vouchers in the Project
                    embed.add_field(
                        name=f'Project ID: **{project_id}**',
                        value='No Vouchers',
                        inline=False,
                        )
                    continue

                for credit_id in credits_id:
                    # We loop over the credits to grab their names
                    voucher = ovh_client.get(
                        f'/cloud/project/{project_id}/credit/{credit_id}'
                        )

                    # We loop over the vouchers to grab their names
                    desc = textwrap.shorten(voucher['description'], width=20, placeholder="...")
                    embed_field_value_table['Voucher'].append(voucher['voucher'])
                    embed_field_value_table['Avail.'].append(voucher['available_credit']['text'])
                    embed_field_value_table['Used'].append(voucher['used_credit']['text'])
                    embed_field_value_table['Description'].append(desc)

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
        pass

@group_pci.command(
    description='Commands related to Project Instances',
    default_permission=False,
    name='instance',
    )
@commands.has_any_role(ROLE_TECH_RO)
@option(
    "action",
    description="Instances action",
    autocomplete=discord.utils.basic_autocomplete(
        [
            discord.OptionChoice("delete", value="delete"),
            discord.OptionChoice("list", value="list"),
            discord.OptionChoice("show", value="show"),
            discord.OptionChoice("create", value="create"),
            ]
        )
    )
@option(
    "projectid",
    description="Project ID",
    autocomplete=get_project_list,
    required=True,
    )
@option(
    "instanceid",
    description="Instance ID",
    autocomplete=get_instance_list,
    required=False,
    )
@option(
    "sshkeyid",
    description="SSH Key ID",
    autocomplete=get_sshkey_list,
    required=False,
    )
async def instance(
    ctx,
    action: str,
    projectid: str,
    instanceid: str,
    sshkeyid: str,
):
    """
    This part performs actions on Public Cloud Instances
    So far:
    - list: Displays the list of ALL Instances
    - show: Displays the details of a specific Instance
    - delete: Deletes a specific Instance
    - create: Creates a new Instance
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
        f'[#{channel}][{name}] /{DISCORD_GROUP_PCI} instance '
        f'{action} {projectid} {instanceid}'
        )

    if action == 'list':
        # This command will require basic TECH_RO role, checked before
        try:
            embed = discord.Embed(
                title=f'**{my_nic}**',
                colour=discord.Colour.green()
                )
            # We start with the headers
            embed_field_value_table = {
                'Instance Name': [],
                'Region': [],
                'Flavor': [],
            }

            project = ovh_client.get(f'/cloud/project/{projectid}')
            if project['status'] == 'suspended':
                # Suspended Projects cannot be queried later
                embed.add_field(
                    name=f'Project ID: **{projectid}**',
                    value='(Suspended)',
                    inline=False,
                    )

            instances = ovh_client.get(
                f'/cloud/project/{projectid}/instance'
                )
            if len(instances) == 0:
                # There is no Instances in the Project
                embed.add_field(
                    name=f'Project ID: **{projectid}**',
                    value='No Instances',
                    inline=False,
                    )
                await ctx.interaction.edit_original_response(
                embed=embed
                )
                return

            # We loop over the instances to grab their names
            for instance in instances:
                if 'nodepool' in instance['name']:
                    # We want to exclude K8s nodepool nodes
                    # Too much trouble if someone mistakenly kills one
                    continue

                embed_field_value_table['Instance Name'].append(instance['name'])
                embed_field_value_table['Region'].append(instance['region'])
                embed_field_value_table['Flavor'].append(instance['planCode'].split('.')[0])

            embed.add_field(
                name=f'Project ID: **{projectid}**',
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
        # This command will require basic TECH_RO role, checked before
        if projectid is None or instanceid is None:
            logger.error('Missing mandatory option(s)')
            msg = (
                'Check that you provided all variables: \n'
                ' - `projectid` \n'
                ' - `instanceid` \n'
                )
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            instance = ovh_client.get(
                f'/cloud/project/{projectid}/instance/{instanceid}'
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
                    f'{json.dumps(instance, indent=4)}'
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

        if projectid is None or instanceid is None:
            logger.error('Missing mandatory option(s)')
            msg = (
                'Check that you provided all variables: \n'
                ' - `projectid` \n'
                ' - `instanceid` \n'
                )
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            instance = ovh_client.get(
                f'/cloud/project/{projectid}/instance/{instanceid}'
                )
            ovh_client.delete(
                f'/cloud/project/{projectid}/instance/{instanceid}'
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
                    f"The Public Cloud Instance "
                    f"`{instance['name']}` in {instance['region']} "
                    f"was deleted"
                    ),
                colour=discord.Colour.green()
            )
            embed.set_footer(text=f"Project ID: {projectid}")

            await ctx.respond(embed=embed)

        logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        return
    elif action == 'create':
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

        if projectid is None or sshkeyid is None:
            logger.error('Missing mandatory option(s)')
            msg = (
                'Check that you provided all variables: \n'
                ' - `projectid` \n'
                ' - `sshkeyid` \n'
                )
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            await ctx.respond(
                "Give me some parameters to fullfill this action:",
                view=InstanceCreationView(ctx, ovh_client, projectid, sshkeyid),
                ephemeral=True,
                )
        except Exception as e:
            msg = f'Command aborted: Instance creation KO [{e}]'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return
        else:
            logger.info('Command successfull: Instance creation OK')
            return


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

@group_hpc.command(
    description='Display Hosted Private Cloud Infrastructures informations',
    default_permission=False,
    name='infrastructure',
    )
@commands.has_any_role(ROLE_TECH_RO)
@option(
    "action",
    description="HPC Infrastructure action",
    autocomplete=discord.utils.basic_autocomplete(
        [
            discord.OptionChoice("list", value="list"),
            discord.OptionChoice("show", value="show"),
            ]
        )
    )
@option(
    "service_name",
    description="Hosted Private Cloud Name",
    autocomplete=get_hpc_list,
    required=False,
    )
async def infrastructure(
    ctx,
    action: str,
    service_name: str,
):
    """
    This part performs actions on Hosted Private Cloud (VMware) Infrastructures
    So far:
    - list: Display the list of ALL Hosted Private Cloud
    - show: When provided a HPC ID, will show its details
    """
    # As we rely on potentially a lot of API calls, we need time to answer
    await ctx.defer()
    # Pre-flight checks: Channel
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(f'[#{channel}][{name}] /{DISCORD_GROUP_PCC} infrastructure {action} {service_name}')

    if action == 'list':
        # This command will require basic TECH_RO role, checked before
        try:
            service_names = ovh_client.get('/dedicatedCloud')
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

            for service_name in service_names:
                hpc = ovh_client.get(f'/dedicatedCloud/{service_name}')
                embed.add_field(
                    name=f'Hosted Private Cloud: **{service_name}**',
                    value=(
                        f"**Version**: {hpc['version']['major'] + hpc['version']['minor']}\n"
                        f"**Location**: {hpc['location']}\n"
                        f"**Description**: {hpc['description']}\n"
                        f"**State**: {hpc['state']}"
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
        # This command will require basic TECH_RO role, checked before
        if service_name is None:
            logger.error('Missing mandatory option(s)')
            msg = (
                'Check that you provided all variables: \n'
                ' - `hpc_name` \n'
                )
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            hpc = ovh_client.get(f'/dedicatedCloud/{service_name}')
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
                    f'{json.dumps(hpc, indent=4)}'
                    f'\n```'
                    ),
                colour=discord.Colour.green()
            )
            await ctx.respond(embed=embed)

        logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        return


@group_hpc.command(
    description='Display Hosted Private Cloud Compute informations',
    default_permission=False,
    name='vm',
    )
@commands.has_any_role(ROLE_TECH_RO)
@option(
    "action",
    description="HPC VM action",
    autocomplete=discord.utils.basic_autocomplete(
        [
            discord.OptionChoice("list", value="list"),
            ]
        )
    )
@option(
    "service_name",
    description="Hosted Private Cloud Name",
    autocomplete=get_hpc_list,
    required=True,
    )
async def hpc_vm(
    ctx,
    action: str,
    service_name: str,
):
    """
    This part performs actions on Hosted Private Cloud (VMware)
    So far:
    - list: Display the list of Compute items
    """
    # As we rely on potentially a lot of API calls, we need time to answer
    await ctx.defer()
    # Pre-flight checks: Channel
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(f'[#{channel}][{name}] /{DISCORD_GROUP_PCC} vm {action} {service_name}')

    # Whatever is the action, we check the service is still active first
    try:
        hpc = ovh_client.get(f'/dedicatedCloud/{service_name}')
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
        if hpc['state'] != "delivered":
            msg = f"This Hosted Private Cloud is in state: `{hpc['state']}`. Cannot be queried"
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

    if action == 'list':
        # This command will require basic TECH_RO role, checked before
        embed = discord.Embed(
                title=f'**{my_nic}**',
                colour=discord.Colour.green()
                )

        try:
            datacenters = ovh_client.get(f'/dedicatedCloud/{service_name}/datacenter')
        except Exception as e:
            msg = f'API calls KO [{e}]'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        # We loop over the datacenters
        hosts = {}
        try:
            embed = discord.Embed(
                title=f'**{my_nic}**',
                colour=discord.Colour.green()
                )

            for datacenter_id in datacenters:
                vms = ovh_client.get(f'/dedicatedCloud/{service_name}/datacenter/{datacenter_id}/vm')

                for vm_id in vms:
                    vm = ovh_client.get(f'/dedicatedCloud/{service_name}/datacenter/{datacenter_id}/vm/{vm_id}')
                    host = f"{vm['clusterName']}/{vm['hostName']}"
                    if host not in hosts:
                        hosts[host] = []
                    hosts[host].append(vm)

            # We loop on hosts to have a better display
            for host, vms in hosts.items():
                # We start with the headers
                embed_field_value_table = {
                    'Name': [],
                    'vCPUs': [],
                    'RAM': [],
                    'State': [],
                }
                for vm in vms:
                    vm_name = textwrap.shorten(vm['name'], width=27, placeholder="...")
                    embed_field_value_table['Name'].append(vm_name)
                    embed_field_value_table['vCPUs'].append(vm['cpuNum'])
                    embed_field_value_table['RAM'].append(vm['memoryMax'])
                    embed_field_value_table['State'].append(vm['powerState'])

                embed.add_field(
                    name=f'Host: **{host}**',
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

                await ctx.interaction.edit_original_response(embed=embed)
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


@group_hpc.command(
    description='Display Hosted Private Cloud Compute informations',
    default_permission=False,
    name='filer',
    )
@commands.has_any_role(ROLE_TECH_RO)
@option(
    "action",
    description="HPC Filer action",
    autocomplete=discord.utils.basic_autocomplete(
        [
            discord.OptionChoice("list", value="list"),
            discord.OptionChoice("show", value="show"),
            ]
        )
    )
@option(
    "service_name",
    description="Hosted Private Cloud Name",
    autocomplete=get_hpc_list,
    required=True,
    )
@option(
    "filer_name",
    description="Filer Name",
    autocomplete=get_hpc_filer_list,
    required=False,
    )
async def filer(
    ctx,
    action: str,
    service_name: str,
    filer_name: str,
):
    """
    This part performs actions on Hosted Private Cloud (VMware)
    So far:
    - list: Display the list of Filer/Datastore items
    """
    # As we rely on potentially a lot of API calls, we need time to answer
    await ctx.defer()
    # Pre-flight checks: Channel
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(f'[#{channel}][{name}] /{DISCORD_GROUP_PCC} filer {action} {service_name}')

    # Whatever is the action, we check the service is still active first
    try:
        hpc = ovh_client.get(f'/dedicatedCloud/{service_name}')
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
        if hpc['state'] != "delivered":
            msg = f"This Hosted Private Cloud is in state: `{hpc['state']}`. Cannot be queried"
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

    if action == 'list':
        # This command will require basic TECH_RO role, checked before
        embed = discord.Embed(
                title=f'**{my_nic}**',
                colour=discord.Colour.green()
                )

        try:
            datacenters = ovh_client.get(f'/dedicatedCloud/{service_name}/datacenter')
        except Exception as e:
            msg = f'API calls KO [{e}]'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        # We start with the headers
        embed_field_value_table = {
            'Name': [],
            'Prov.': [],
            'Used': [],
            'Free': [],
            'Total': [],
        }

        # We loop over the datacenters
        try:
            embed = discord.Embed(
                title=f'**{my_nic}**',
                colour=discord.Colour.green()
                )

            for datacenter_id in datacenters:
                filers = ovh_client.get(
                    f'/dedicatedCloud/{service_name}/datacenter/{datacenter_id}/filer'
                    )

                for filer_id in filers:
                    filer = ovh_client.get(
                        f'/dedicatedCloud/{service_name}/datacenter/{datacenter_id}/filer/{filer_id}'
                        )

                    embed_field_value_table['Name'].append(filer['name'])
                    embed_field_value_table['Prov.'].append(f"{filer['spaceProvisionned']}{filer['size']['unit']}")
                    embed_field_value_table['Used'].append(f"{filer['spaceUsed']}{filer['size']['unit']}")
                    embed_field_value_table['Free'].append(f"{filer['spaceFree']}{filer['size']['unit']}")
                    embed_field_value_table['Total'].append(f"{filer['size']['value']}{filer['size']['unit']}")

                embed.add_field(
                    name=f'Datacenter: **{service_name}/datacenter{datacenter_id}**',
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

                await ctx.interaction.edit_original_response(embed=embed)
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
        # This command will require basic TECH_RO role, checked before
        if service_name is None or filer_name is None:
            logger.error('Missing mandatory option(s)')
            msg = (
                'Check that you provided all variables: \n'
                ' - `service_name` \n'
                ' - `filer_name` \n'
                )
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            # Be careful, short hacking here, the filer_name includes as a prefix the DC ID
            # filer_name: 'datacenter_id/filer_name'
            # So we need to extract it
            m = re.search(r"^(?P<datacenter_id>\d+)/(?P<filer_name>\d+)", filer_name)
            if m is None:
                msg = f'Datacenter ID and/or Filer Name not found ({filer_name})'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return
            filer = ovh_client.get(
                f'/dedicatedCloud/{service_name}'
                f"/datacenter/{m.group('datacenter_id')}"
                f"/filer/{m.group('filer_name')}"
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
                    f'{json.dumps(filer, indent=4)}'
                    f'\n```'
                    ),
                colour=discord.Colour.green()
            )
            await ctx.respond(embed=embed)

        logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        return

@group_hpc.command(
    description='Display Hosted Private Cloud User informations',
    default_permission=False,
    name='user',
    )
@commands.has_any_role(ROLE_TECH_RO)
@option(
    "action",
    description="HPC User action",
    autocomplete=discord.utils.basic_autocomplete(
        [
            discord.OptionChoice("list", value="list"),
            discord.OptionChoice("show", value="show"),
            ]
        )
    )
@option(
    "service_name",
    description="Hosted Private Cloud Name",
    autocomplete=get_hpc_list,
    required=True,
    )
@option(
    "user_name",
    description="User Name",
    autocomplete=get_hpc_user_list,
    required=False,
    )
async def hpc_user(
    ctx,
    action: str,
    service_name: str,
    user_name: str,
):
    """
    This part performs actions on Hosted Private Cloud (VMware)
    So far:
    - list: Display the list of Users
    """
    # As we rely on potentially a lot of API calls, we need time to answer
    await ctx.defer()
    # Pre-flight checks: Channel
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(f'[#{channel}][{name}] /{DISCORD_GROUP_PCC} filer {action} {service_name}')

    # Whatever is the action, we check the service is still active first
    try:
        hpc = ovh_client.get(f'/dedicatedCloud/{service_name}')
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
        if hpc['state'] != "delivered":
            msg = f"This Hosted Private Cloud is in state: `{hpc['state']}`. Cannot be queried"
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

    if action == 'list':
        # This command will require basic TECH_RO role, checked before
        embed = discord.Embed(
                title=f'**{my_nic}**',
                colour=discord.Colour.green()
                )

        try:
            users = ovh_client.get(f'/dedicatedCloud/{service_name}/user')
        except Exception as e:
            msg = f'API calls KO [{e}]'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        # We loop over the users
        try:
            for user_id in users:
                user = ovh_client.get(f'/dedicatedCloud/{service_name}/user/{user_id}')

                embed.add_field(
                    name=f"👤 {user['login']}",
                    value=(
                        f"Permissions:\n"
                        f"> **Network**: {user['canManageNetwork']}\n"
                        f"> **FailOver IP**: {user['canManageIpFailOvers']}\n"
                        f"> **NSX**: {user['nsxRight']}\n"
                        f"> **Encryption**: {user['encryptionRight']}\n"
                        f"Activation: {user['activationState']}\n"
                        f"State: {user['state']}\n"
                        ),
                    inline=True,
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
        # This command will require basic TECH_RO role, checked before
        if service_name is None:
            logger.error('Missing mandatory option(s)')
            msg = (
                'Check that you provided all variables: \n'
                ' - `service_name` \n'
                ' - `user_name` \n'
                )
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await ctx.respond(embed=embed)
            return

        try:
            user = ovh_client.get(f'/dedicatedCloud/{service_name}/user/{user_name}')
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

#
# Run Discord bot
#
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    logger.error(f'Discord bot.run KO [{e}]')
