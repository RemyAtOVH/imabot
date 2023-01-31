# -*- coding: utf8 -*-

"""Module to locate all Autocomplete lists."""
import os

import discord

from loguru import logger

from variables import (
    ANSIBLE_PLAYBOOK_FOLDER,
)

#
# Ansible related Autocomplete lists
#

async def get_playbook_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of Ansible Playbooks. """
    playbook_list = []

    if not os.path.isdir(ANSIBLE_PLAYBOOK_FOLDER):
        msg = f'ANSIBLE_PLAYBOOK_FOLDER does dot exists ({ANSIBLE_PLAYBOOK_FOLDER})'
        logger.warning(msg)
        return playbook_list

    try:
        playbooks = os.listdir(ANSIBLE_PLAYBOOK_FOLDER)
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if playbooks is None or len(playbooks) == 0:
            return []
        else:
            for playbook in playbooks:
                playbook_list.append(
                    discord.OptionChoice(
                        f"📝 {playbook}",
                        value=playbook,
                        )
                    )
            return playbook_list
