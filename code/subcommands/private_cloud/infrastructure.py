"""
Discord command definition for /{DISCORD_GROUP_PCC} infrastructure
"""
import json

import discord

from discord.commands import option
from discord.ext import commands
from loguru import logger

from variables import (
    DISCORD_GROUP_PCC,
    ROLE_TECH_RO,
)

from ._autocomplete import (
    get_hpc_list,
)

def infrastructure(group_hpc, ovh_client, my_nic):
    """
    Discord command definition for /{DISCORD_GROUP_PCC} infrastructure
    """
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
        logger.info(
            f'[#{channel}][{name}] /{DISCORD_GROUP_PCC} '
            f'infrastructure {action} {service_name}'
            )

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
