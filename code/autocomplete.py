# -*- coding: utf8 -*-

"""Module to locate all Autocomplete lists."""

import discord
import ovh

from loguru import logger

from variables import (
    OVH_AK,
    OVH_AS,
    OVH_CK,
    OVH_ENDPOINT,
)

async def get_project_list(ctx: discord.AutocompleteContext):
    """Function to build and serve an Autocomplete list of Projects."""
    try:
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )

        projects_id = ovh_client.get('/cloud/project')
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if projects_id is None or len(projects_id) == 0:
            return []

        project_list = []
        for project_id in projects_id:
            project_list.append(
                discord.OptionChoice(
                    project_id,
                    value=project_id,
                    )
                )

        return project_list

async def get_user_list(ctx: discord.AutocompleteContext):
    """Function to build and serve an Autocomplete list of Users."""
    try:
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )

        users = ovh_client.get(
            f'/cloud/project/{ctx.options["projectid"]}/user'
            )
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if users is None or len(users) == 0:
            return []

        user_list = []
        for user in users:
            user_list.append(
                discord.OptionChoice(
                    f"{user['username']} ({user['description']})",
                    value=f"{user['id']}",
                    )
                )

        return user_list
