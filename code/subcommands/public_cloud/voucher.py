"""
Discord command definition for /{DISCORD_GROUP_PCI} voucher
"""
import textwrap

import discord

from discord.commands import option
from discord.ext import commands
from loguru import logger
from tabulate import tabulate

from variables import (
    DISCORD_GROUP_PCI,
    ROLE_ACCOUNTING,
)

from ._autocomplete import (
    get_project_list,
    get_voucher_list,
)

def voucher(group_pci, ovh_client, my_nic):
    """
    Discord command definition for /{DISCORD_GROUP_PCI} voucher
    """
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
                        desc = textwrap.shorten(
                            voucher['description'],
                            width=20,
                            placeholder="...",
                            )
                        embed_field_value_table['Description'].append(desc)

                        embed_field_value_table['Voucher'].append(
                            voucher['voucher']
                            )
                        embed_field_value_table['Avail.'].append(
                            voucher['available_credit']['text']
                            )
                        embed_field_value_table['Used'].append(
                            voucher['used_credit']['text']
                            )

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
