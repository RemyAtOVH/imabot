"""
Discord command definition for /{DISCORD_GROUP_PCI} user
"""
import json

import discord

from discord.commands import option
from discord.ext import commands
from loguru import logger
from tabulate import tabulate

from variables import (
    DISCORD_GROUP_PCI,
    ROLE_TECH_RO,
    ROLE_TECH_RW,
)

from ._autocomplete import (
    get_project_list,
    get_user_list,
)

def user(group_pci, ovh_client, my_nic):
    """
    Discord command definition for /{DISCORD_GROUP_PCI} user
    """
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
