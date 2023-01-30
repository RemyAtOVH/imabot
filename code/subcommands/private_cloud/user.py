"""
Discord command definition for /{DISCORD_GROUP_PCC} user
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
    get_hpc_user_list,
)


def user(group_hpc, ovh_client, my_nic):
    """
    Discord command definition for /{DISCORD_GROUP_PCC} user
    """
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
