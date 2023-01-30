"""
Discord command definition for /{DISCORD_GROUP_PCC} filer
"""
import json
import os
import re

import discord

from discord.commands import option
from discord.ext import commands
from loguru import logger
from tabulate import tabulate

from variables import (
    DISCORD_GROUP_PCC,
    ROLE_TECH_RO,
)

from ._autocomplete import (
    get_hpc_list,
    get_hpc_filer_list,
)


def filer(group_hpc, ovh_client, my_nic):
    """
    Discord command definition for /{DISCORD_GROUP_PCC} filer
    """
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
                            f'/dedicatedCloud/{service_name}'
                            f'/datacenter/{datacenter_id}/filer/{filer_id}'
                            )

                        embed_field_value_table['Name'].append(
                                filer['name']
                                )
                        embed_field_value_table['Prov.'].append(
                            f"{filer['spaceProvisionned']}{filer['size']['unit']}"
                            )
                        embed_field_value_table['Used'].append(
                            f"{filer['spaceUsed']}{filer['size']['unit']}"
                            )
                        embed_field_value_table['Free'].append(
                            f"{filer['spaceFree']}{filer['size']['unit']}"
                            )
                        embed_field_value_table['Total'].append(
                            f"{filer['size']['value']}{filer['size']['unit']}"
                            )

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
