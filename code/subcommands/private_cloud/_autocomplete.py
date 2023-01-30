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

#
# Private Cloud related Autocomplete lists
#

async def get_hpc_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of HPC. """
    try:
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )

        service_names = ovh_client.get(
            '/dedicatedCloud'
            )
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if service_names is None or len(service_names) == 0:
            return []

        hpc_list = []
        for service_name in service_names:
            hpc_list.append(
                discord.OptionChoice(f"🏢 {service_name}", value=service_name)
                )

        return hpc_list

async def get_hpc_user_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of Vouchers. """
    try:
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )
        users_id = ovh_client.get(
            f'/dedicatedCloud/{ctx.options["service_name"]}'
            f'/user'
            )
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if users_id is None or len(users_id) == 0:
            return []

        user_list = []
        for user_id in users_id:
            user = ovh_client.get(
                f'/dedicatedCloud/{ctx.options["service_name"]}'
                f'/user/{user_id}'
                )
            user_list.append(
                discord.OptionChoice(
                    f"👤 {user['login']}",
                    value=f"{user['userId']}",
                    )
                )
        return user_list

async def get_hpc_filer_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of Filers. """
    try:
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )
        datacenters_id = ovh_client.get(
            f'/dedicatedCloud/{ctx.options["service_name"]}'
            f'/datacenter'
            )
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if datacenters_id is None or len(datacenters_id) == 0:
            return []

        filer_list = []
        for datacenter_id in datacenters_id:
            filers_id = ovh_client.get(
                f'/dedicatedCloud/{ctx.options["service_name"]}'
                f'/datacenter/{datacenter_id}/filer'
                )
            for filer_id in filers_id:
                filer = ovh_client.get(
                    f'/dedicatedCloud/{ctx.options["service_name"]}'
                    f'/datacenter/{datacenter_id}/filer/{filer_id}'
                    )
                filer_list.append(
                    discord.OptionChoice(
                        f"🗄️ {filer['name']}",
                        value=f"{datacenter_id}/{filer['filerId']}",
                        )
                    )
        return filer_list
