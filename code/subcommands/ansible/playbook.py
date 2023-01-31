"""
Discord command definition for /{DISCORD_GROUP_ANSIBLE} playbook
"""
import subprocess
import os.path

import discord

from discord.commands import option
from discord.ext import commands
from loguru import logger

from variables import (
    ANSIBLE_HOSTS_FILE,
    ANSIBLE_PLAYBOOK_FOLDER,
    DISCORD_GROUP_ANSIBLE,
    ROLE_TECH_RW,
)

from ._autocomplete import (
    get_playbook_list,
)

def playbook(group_ansible):
    """
    Discord command definition for /{DISCORD_GROUP_ANSIBLE} playbook
    """
    @group_ansible.command(
        description='Commands related to Ansible playbook',
        default_permission=False,
        name='playbook',
        )
    @commands.has_any_role(ROLE_TECH_RW)
    @option(
        "action",
        description="Ansible Playbook action",
        autocomplete=discord.utils.basic_autocomplete(
            [
                discord.OptionChoice("check", value="check"),
                discord.OptionChoice("hosts", value="hosts"),
                discord.OptionChoice("list", value="list"),
                discord.OptionChoice("run", value="run"),
                discord.OptionChoice("show", value="show"),
                ]
            )
        )
    @option(
        "playbook",
        description="Ansible Playbook File",
        autocomplete=get_playbook_list,
        required=False,
        )
    async def playbook(
        ctx,
        action: str,
        playbook: str,
    ):
        """
        This part performs actions on Ansible Playbooks
        So far:
        - list: Lists all Playbooks present in ANSIBLE_PLAYBOOK_FOLDER
        - show: Displays the contents of the selected Playbook
        - run: Runs the selected Playbook
        - check: Checks the selected Playbook
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
            f'[#{channel}][{name}] /{DISCORD_GROUP_ANSIBLE} playbook '
            f'{action} {playbook}'
            )

        if action == 'list':
            # This command will require basic TECH_RW role, checked before
            if not os.path.isdir(ANSIBLE_PLAYBOOK_FOLDER):
                msg = f'ANSIBLE_PLAYBOOK_FOLDER does dot exists ({ANSIBLE_PLAYBOOK_FOLDER})'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return

            try:
                playbooks = os.listdir(ANSIBLE_PLAYBOOK_FOLDER)
                description = ''
                for playbook in playbooks:
                    description += f'`{playbook}`\n'

                embed = discord.Embed(
                    title=f'**Playbooks**: {ANSIBLE_PLAYBOOK_FOLDER}',
                    colour=discord.Colour.green(),
                    description=description,
                    )
                await ctx.interaction.edit_original_response(
                    embed=embed
                    )
            except Exception as e:
                msg = f'Playbook list generation KO [{e}]'
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
            # This command will require basic TECH_RW role, checked before
            playbook_path = f"{ANSIBLE_PLAYBOOK_FOLDER}/{playbook}"
            if not os.path.isfile(playbook_path):
                msg = f'Playbook does not exists ({playbook_path})'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return

            with open(playbook_path, "r", encoding='utf8') as playbookfile:
                embed = discord.Embed(
                    description=(
                        f'```yaml\n'
                        f'{playbookfile.read()}'
                        f'\n```'
                        ),
                    colour=discord.Colour.green()
                )
            playbookfile.close()
            await ctx.respond(embed=embed)
            logger.debug(f'[#{channel}][{name}] └──> Queries OK')
        elif action == 'check':
            # This command will require basic TECH_RW role, checked before
            playbook_path = f"{ANSIBLE_PLAYBOOK_FOLDER}/{playbook}"
            if not os.path.isfile(playbook_path):
                msg = f'Playbook does not exists ({playbook_path})'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return

            try:
                res = subprocess.run(
                    [
                        "ansible-playbook",
                        f"--inventory-file={ANSIBLE_HOSTS_FILE}",
                        "--user=ansible",
                        f"{playbook_path}",
                        "--check",
                        ],
                    capture_output=True,
                    check=True,
                    env=os.environ,
                    )
            except Exception as e:
                msg = f'asnsible-playbook command KO [{e}]'
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
        elif action == 'run':
            # This command will require basic TECH_RW role, checked before
            playbook_path = f"{ANSIBLE_PLAYBOOK_FOLDER}/{playbook}"
            if not os.path.isfile(playbook_path):
                msg = f'Playbook does not exists ({playbook_path})'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return

            try:
                res = subprocess.run(
                    [
                        "ansible-playbook",
                        f"--inventory-file={ANSIBLE_HOSTS_FILE}",
                        "--user=ansible",
                        f"{playbook_path}",
                        ],
                    capture_output=True,
                    check=True,
                    )
            except Exception as e:
                msg = f'asnsible-playbook command KO [{e}]'
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
        elif action == 'hosts':
            # This command will require basic TECH_RW role, checked before
            playbook_path = f"{ANSIBLE_PLAYBOOK_FOLDER}/{playbook}"
            if not os.path.isfile(playbook_path):
                msg = f'Playbook does not exists ({playbook_path})'
                logger.error(msg)
                embed = discord.Embed(
                    description=msg,
                    colour=discord.Colour.red()
                )
                await ctx.respond(embed=embed)
                return

            try:
                res = subprocess.run(
                    [
                        "ansible-playbook",
                        f"--inventory-file={ANSIBLE_HOSTS_FILE}",
                        "--user=ansible",
                        f"{playbook_path}",
                        "--list-hosts",
                        ],
                    capture_output=True,
                    check=True,
                    )
            except Exception as e:
                msg = f'asnsible-playbook command KO [{e}]'
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
