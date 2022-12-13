#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""🤖 Module to build Discord interactions and automate IT actions 🤖."""

import json
import textwrap

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
    DISCORD_GROUP_GLOBAL,
    OVH_AK,
    OVH_AS,
    OVH_CK,
    OVH_ENDPOINT,
    ROLE_TECH_RO,
    ROLE_TECH_RW,
    ROLE_ACCOUNTING,
)

from autocomplete import (
    get_project_list,
    get_user_list,
    get_voucher_list,
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
# /ovh Slash Commands
#
try:
    group_global = bot.create_group(
        description="Commands related to OVHcloud requests",
        name=DISCORD_GROUP_GLOBAL,
        )
except Exception as e:
    logger.error(f'Group KO (/{DISCORD_GROUP_GLOBAL}) [{e}]')
else:
    logger.debug(f'Group OK (/{DISCORD_GROUP_GLOBAL})')

@group_global.command(
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
    logger.info(f'[#{channel}][{name}] /ovh project {projectid}')

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

@group_global.command(
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
    # Pre-flight checks: Channel
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

@group_global.command(
    description='/ovh Commands related to Project Vouchers',
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
        f'[#{channel}][{name}] /ovh voucher '
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

@group_global.command(
    description='/ovh Commands related to Project Billing',
    default_permission=False,
    name='billing',
    )
@commands.has_any_role(ROLE_ACCOUNTING)
async def billing(
    ctx,
):
    """This part performs actions on Public Cloud billing."""
    # As we rely on potentially a lot of API calls, we need time to answer
    await ctx.defer()
    # Pre-flight checks
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(f'[#{channel}][{name}] /ovh billing')

    try:
        embed = discord.Embed(
            title=f'**{my_nic}**',
            colour=discord.Colour.green()
            )

        debts_id = ovh_client.get('/me/debtAccount/debt')
        if len(debts_id) == 0:
            # There is no Debt at all on the NIC
            embed.add_field(
                name='',
                value='No Debt/Current billing',
                inline=False,
                )

        for debt_id in debts_id:
            # We start with the headers
            embed_field_value_table = {
                'Type': [],
                'Description': [],
                'Price': [],
                }

            # We locate the debt to have the initial orderId
            debt = ovh_client.get(
                f'/me/debtAccount/debt/{debt_id}'
                )
            order_id = debt['orderId']
            # With the orderId, we grab the orderDetailIds
            detailed_orders_id = ovh_client.get(
                f'/me/order/{order_id}/details'
                )

            for detailed_order_id in detailed_orders_id:
                # We loop over the detailed orders to grab the infos
                detailed_order = ovh_client.get(
                f'/me/order/{order_id}/details/{detailed_order_id}'
                )
                project_id = detailed_order['domain']
                desc = textwrap.shorten(detailed_order['description'], width=27, placeholder="...")
                embed_field_value_table['Type'].append(detailed_order['detailType'])
                embed_field_value_table['Price'].append(detailed_order['totalPrice']['text'])
                embed_field_value_table['Description'].append(desc)

            embed.add_field(
                name=f'Project ID: **{project_id}**\nOrder ID: **{order_id}**',
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

@group_global.command(
    description='Command to display Bot settings (API keys, roles, ...)',
    default_permission=False,
    name='settings',
    )
async def settings(
    ctx,
):
    """This part performs checks and display info on bot config."""
    # As we rely on potentially a lot of API calls, we need time to answer
    await ctx.defer()
    # Pre-flight checks
    if ctx.channel.type is discord.ChannelType.private:
        channel = ctx.channel.type
    else:
        channel = ctx.channel.name
    name = ctx.author.name
    logger.info(f'[#{channel}][{name}] /settings')

    embed = discord.Embed(
            title='**Bot settings**',
            colour=discord.Colour.blue()
            )

    try:
        # Lets check OVHcloud API credentials
        if any([
            OVH_ENDPOINT is None,
            OVH_AK is None,
            OVH_AS is None,
            OVH_CK is None,
        ]):
            # At least one of the credentials info is missing
            value_credentials=(
                ':warning: '
                'One of your OVHcloud API credentials is missing.\n'
                'Check your ENV vars!'
                )
    except Exception as e:
        msg = f'Credentials loading KO [{e}]'
        logger.error(msg)
        value_credentials=f':no_entry: {e}'
    else:
        # Everything is OK
        value_credentials = (
            ':white_check_mark: '
            'Your OVHcloud API credentials are set up!'
            )
    embed.add_field(
        name='Credentials',
        value=value_credentials,
        inline=False,
        )

    try:
        # Lets check OVHcloud API connection status
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )
        me = ovh_client.get('/me')
        # At least one of the credentials info is missing
        if me is None or me['nichandle'] is None:
            value_auth=(
                ':warning: '
                'Unable to authenticate to OVHcloud API.\n'
                'Check the validity of your credentials!'
                )
    except Exception as e:
        msg = f'OVHcloud API calls KO [{e}]'
        logger.error(msg)
        value_auth=f':no_entry: {e}'
    else:
        # Everything is OK
        value_auth = (
            ':white_check_mark: '
            "Authentication to OVHcloud API successfull! "
            f"(**{me['nichandle']}**)"
            )
    embed.add_field(
        name='Authentication',
        value=value_auth,
        inline=False,
        )

    try:
        # We answer
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

#
# Run Discord bot
#
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    logger.error(f'Discord bot.run KO [{e}]')
