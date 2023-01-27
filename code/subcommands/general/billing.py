"""
Discord ommand definition for:
/{DISCORD_GROUP_GENERAL} billing
"""
import os
import textwrap
import datetime

import discord
import pytz

from discord.commands import option
from discord.ext import commands

from loguru import logger
from tabulate import tabulate

DISCORD_GROUP_GENERAL = os.environ.get("DISCORD_GROUP_GENERAL", 'iamabot')
ROLE_ACCOUNTING = os.environ.get("DISCORD_ROLE_ACCOUNTING", "Accounting")

def billing(group_global, ovh_client, my_nic):
    @group_global.command(
    description='Commands related to Project Billing',
    default_permission=False,
    name='billing',
    )
    @option(
        "debt_status",
        description="Selects the type of debt you want to list." ,
        autocomplete=discord.utils.basic_autocomplete(
            [
                discord.OptionChoice("ALL", value="all"),
                discord.OptionChoice("Unpaid only", value="unpaid"),
                ]
            )
        )
    @option(
        "debt_period",
        description="Selects the period of debts you want to list." ,
        autocomplete=discord.utils.basic_autocomplete(
            [
                discord.OptionChoice("30 days", value="30"),
                discord.OptionChoice("60 days", value="60"),
                discord.OptionChoice("90 days", value="90"),
                discord.OptionChoice("365 days", value="365"),
                ]
            )
        )
    @commands.has_any_role(ROLE_ACCOUNTING)
    async def billing(
        ctx,
        debt_status: str,
        debt_period: str,
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
        logger.info(f'[#{channel}][{name}] /{DISCORD_GROUP_GENERAL} billing')

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

            debt_counter = 0  # Used to track if we skipped all content or not

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

                # Depending on the Discord request, we may dismiss some results
                if debt_status == 'unpaid' and debt['status'] != 'UNPAID':
                    continue
                else:
                    order_id = debt['orderId']

                # Limiting output based on debt_period Selector
                order_dt = datetime.datetime.fromisoformat(debt['date'])
                now_dt = datetime.datetime.now(pytz.utc)
                days_since = int((now_dt - order_dt).total_seconds() / 86400.0)
                if days_since > int(debt_period):
                    continue

                # With the orderId, we grab the orderDetailIds
                detailed_orders_id = ovh_client.get(
                    f'/me/order/{order_id}/details'
                    )

                # We loop over the detailed orders to grab the infos
                for detailed_order_id in detailed_orders_id:
                    detailed_order = ovh_client.get(
                    f'/me/order/{order_id}/details/{detailed_order_id}'
                    )
                    project_id = detailed_order['domain']
                    desc = textwrap.shorten(
                        detailed_order['description'],
                        width=27,
                        placeholder="...",
                        )
                    embed_field_value_table['Type'].append(detailed_order['detailType'])
                    embed_field_value_table['Price'].append(detailed_order['totalPrice']['text'])
                    embed_field_value_table['Description'].append(desc)

                embed.add_field(
                    name=(
                        f'Project ID: **{project_id}** '
                        f'@({order_dt.strftime("%Y-%m-%d %H:%M:%S")})\n'
                        f'Debt ID: **{debt_id}** | '
                        f'Order ID: **{order_id}** | '
                        f"Status: **{debt['status']}**"
                        ),
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
                debt_counter += 1
                await ctx.interaction.edit_original_response(embed=embed)

            # There was debts, but not showned due to limiting
            if debt_counter == 0:
                embed.add_field(
                    name='',
                    value='No Debt/Current billing matching status & date criteria',
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
