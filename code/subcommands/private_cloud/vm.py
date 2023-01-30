"""
Discord command definition for /{DISCORD_GROUP_PCC} vm
"""
import textwrap

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
)


def vm(group_hpc, ovh_client, my_nic):
    """
    Discord command definition for /{DISCORD_GROUP_PCC} vm
    """
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
                    vms = ovh_client.get(
                        f'/dedicatedCloud/{service_name}'
                        f'/datacenter/{datacenter_id}/vm'
                        )

                    for vm_id in vms:
                        vm = ovh_client.get(
                            f'/dedicatedCloud/{service_name}'
                            f'/datacenter/{datacenter_id}/vm/{vm_id}'
                            )
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
