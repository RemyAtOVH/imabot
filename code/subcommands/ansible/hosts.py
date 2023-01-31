"""
Discord command definition for /{DISCORD_GROUP_ANSIBLE} hosts
"""
import configparser
import subprocess
import os.path

import discord

from discord.commands import option
from discord.ext import commands
from loguru import logger

from variables import (
    ANSIBLE_HOSTS_FILE,
    DISCORD_GROUP_ANSIBLE,
    ROLE_TECH_RW,
)


def hosts(group_ansible):
    """
    Discord command definition for /{DISCORD_GROUP_ANSIBLE} hosts
    """
    @group_ansible.command(
        description='Commands related to Ansible hosts',
        default_permission=False,
        name='hosts',
        )
    @commands.has_any_role(ROLE_TECH_RW)
    @option(
        "action",
        description="Ansible hosts action",
        autocomplete=discord.utils.basic_autocomplete(
            [
                discord.OptionChoice("assign", value="assign"),
                discord.OptionChoice("graph", value="graph"),
                discord.OptionChoice("ping", value="ping"),
                discord.OptionChoice("remove", value="remove"),
                discord.OptionChoice("show", value="show"),
                ]
            )
        )
    @option(
        "section",
        description="Ansible inventory section",
        required=False,
        )
    @option(
        "host",
        description="Ansible host",
        required=False,
        )
    async def hosts(
        ctx,
        action: str,
        section: str,
        host: str,
    ):
        """
        This part performs actions on Ansible hosts
        So far:
        - assign: Assigns a host in section (creates new section if needed)
        - show: Displays the contents of ANSIBLE_HOSTS_FILE
        - remove: Removes a host of a section
        - graph: Displays `ansible --graph` execution
        - ping: Displays `ansible --ping` execution
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
            f'[#{channel}][{name}] /{DISCORD_GROUP_ANSIBLE} hosts '
            f'{action} {section} {host}'
            )

        if action == 'show':
            # This command will require basic TECH_RW role, checked before
            if not os.path.isfile(ANSIBLE_HOSTS_FILE):
                msg = f'ANSIBLE_HOSTS_FILE do not exists ({ANSIBLE_HOSTS_FILE})'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return

            with open(ANSIBLE_HOSTS_FILE, "r", encoding='utf8') as hostsfile:
                embed = discord.Embed(
                    description=(
                        f'```ini\n'
                        f'{hostsfile.read()}'
                        f'\n```'
                        ),
                    colour=discord.Colour.green()
                )
            hostsfile.close()
            await ctx.respond(embed=embed)
            logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        elif action == 'assign':
            if section is None or host is None:
                logger.error('Missing mandatory option(s)')
                msg = (
                    'Check that you provided all variables: \n'
                    ' - `section` \n'
                    ' - `host` \n'
                    )
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return

            if not os.path.isfile(ANSIBLE_HOSTS_FILE):
                command = "x"
            else:
                command = "w"

            try:
                config = configparser.ConfigParser(allow_no_value=True)
                # We load
                config.read_file(open(ANSIBLE_HOSTS_FILE, 'r', encoding='utf8'))
                # We add the section if not exists
                if not config.has_section(section):
                    config.add_section(section)
                # We assign the host inside
                config.set(section, host, None)
                # We write
                config.write(open(ANSIBLE_HOSTS_FILE, command, encoding='utf8'))
            except Exception as e:
                msg = f'Host assign KO [{e}]'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return
            else:
                embed = discord.Embed(
                    description=f'Host `[{host}]` assigned in `[{section}]`',
                    colour=discord.Colour.green()
                )
                await ctx.respond(embed=embed)
                logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        elif action == 'remove':
            if section is None or host is None:
                logger.error('Missing mandatory option(s)')
                msg = (
                    'Check that you provided all variables: \n'
                    ' - `section` \n'
                    ' - `host` \n'
                    )
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return

            try:
                config = configparser.ConfigParser(allow_no_value=True)
                # We load
                config.read_file(open(ANSIBLE_HOSTS_FILE, 'r', encoding='utf8'))
                # We check the section exists
                if not config.has_section(section):
                    msg = f'Section not found [{e}]'
                    logger.error(msg)
                    embed = discord.Embed(
                        description=msg,
                        colour=discord.Colour.orange()
                    )
                    await ctx.respond(embed=embed)
                    return
                # We search for the host
                if config.has_option(section, host):
                    # We remove the host
                    config.remove_option(section, host)
                else:
                    msg = f'Host not found [{e}]'
                    logger.error(msg)
                    embed = discord.Embed(
                        description=msg,
                        colour=discord.Colour.orange()
                    )
                    await ctx.respond(embed=embed)
                    return
                # We write
                config.write(open(ANSIBLE_HOSTS_FILE, 'w', encoding='utf8'))
            except Exception as e:
                msg = f'Host remove KO [{e}]'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return
            else:
                embed = discord.Embed(
                    description=f'Host `{host}` removed from `[{section}]`',
                    colour=discord.Colour.green()
                )
                await ctx.respond(embed=embed)
                logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        elif action == 'graph':
            try:
                res = subprocess.run(
                    [
                        "ansible-inventory",
                        f"--inventory-file={ANSIBLE_HOSTS_FILE}",
                        "--graph"
                        ],
                    capture_output=True,
                    check=True
                    )
            except Exception as e:
                msg = f'Host remove KO [{e}]'
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
                        f'```\n'
                        f"{res.stdout.decode('ascii')}"
                        f'\n```'
                        ),
                    colour=discord.Colour.green()
                )
                await ctx.respond(embed=embed)
                logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        elif action == 'ping':
            try:
                res = subprocess.run(
                    [
                        "ansible",
                        f"--inventory-file={ANSIBLE_HOSTS_FILE}",
                        "all",
                        "--module-name=ping",
                        "--user=ansible",
                        ],
                    capture_output=True,
                    check=True,
                    )
            except Exception as e:
                msg = f'Host remove KO [{e}]'
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
                        f'```\n'
                        f"{res.stdout.decode('ascii')}"
                        f'\n```'
                        ),
                    colour=discord.Colour.green()
                )
                await ctx.respond(embed=embed)
                logger.debug(f'[#{channel}][{name}] └──> Queries OK')
