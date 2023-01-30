"""
Discord command definition for /{DISCORD_GROUP_PCI} project
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
)

from ._autocomplete import (
    get_project_list,
)


def project(group_pci, ovh_client, my_nic):
    """
    Discord command definition for /{DISCORD_GROUP_PCI} project
    """
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
