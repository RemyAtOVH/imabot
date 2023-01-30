"""
Discord command definition for /{DISCORD_GROUP_PCI} instance
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
    get_instance_list,
    get_project_list,
    get_sshkey_list,
)
from ._views import InstanceCreationView

def instance(group_pci, ovh_client, my_nic):
    """
    Discord command definition for /{DISCORD_GROUP_PCI} instance
    """
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
