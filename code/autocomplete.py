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

async def get_instance_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of Project Instances. """
    instance_list = []

    if ctx.options["projectid"] is None:
        return instance_list

    try:
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )

        instances = ovh_client.get(
            f'/cloud/project/{ctx.options["projectid"]}/instance'
            )
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if instances is None or len(instances) == 0:
            return []
        else:
            for instance in instances:
                if 'nodepool' in instance['name']:
                    # We want to exclude K8s nodepool nodes
                    # Too much trouble if someone mistakenly kills one
                    continue

                instance_list.append(
                discord.OptionChoice(
                    f"⚙️ {instance['name']} ({instance['id']})",
                    value=instance['id'],
                    )
                )
            return instance_list


async def get_sshkey_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of SSH Keys. """
    sshkey_list = []

    if ctx.options["projectid"] is None:
        return sshkey_list

    try:
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )

        sshkeys = ovh_client.get(
            f'/cloud/project/{ctx.options["projectid"]}/sshkey'
            )
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if sshkeys is None or len(sshkeys) == 0:
            return sshkey_list
        else:
            for sshkey in sshkeys:
                sshkey_list.append(
                    discord.OptionChoice(f"🔐 {sshkey['name']}", value=f"{sshkey['id']}")
                    )
            return sshkey_list


async def get_project_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of Projects. """
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
                discord.OptionChoice(f"📂 {project_id}", value=project_id)
                )

        return project_list

async def get_user_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of Users. """
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
                    f"👤 {user['description']} ({user['username']})",
                    value=f"{user['id']}",
                    )
                )

        return user_list

async def get_voucher_list(ctx: discord.AutocompleteContext):
    """ Function to build and serve an Autocomplete list of Vouchers. """
    try:
        ovh_client = ovh.Client(
            endpoint=OVH_ENDPOINT,
            application_key=OVH_AK,
            application_secret=OVH_AS,
            consumer_key=OVH_CK,
            )
        credits_id = ovh_client.get(
            f'/cloud/project/{ctx.options["projectid"]}/credit'
            )
    except Exception as e:
        logger.error(f'Autocomplete generation KO [{e}]')
        return []
    else:
        if credits is None or len(credits) == 0:
            return []
        else:
            voucher_list = []
            for credit_id in credits_id:
                credit = ovh_client.get(
                    f'/cloud/project/{ctx.options["projectid"]}'
                    f'/credit/{credit_id}'
                    )
                voucher_list.append(
                    discord.OptionChoice(
                        f"💳 {credit['id']} ({credit['voucher']})",
                        value=f"{credit['id']}",
                        )
                    )
            return voucher_list

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

        service_names = ovh_client.get('/dedicatedCloud')
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
            f'/dedicatedCloud/{ctx.options["service_name"]}/user'
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
                f'/dedicatedCloud/{ctx.options["service_name"]}/user/{user_id}'
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
            f'/dedicatedCloud/{ctx.options["service_name"]}/datacenter'
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
                f'/dedicatedCloud/{ctx.options["service_name"]}/datacenter/{datacenter_id}/filer'
                )
            for filer_id in filers_id:
                filer = ovh_client.get(
                    f'/dedicatedCloud/{ctx.options["service_name"]}/datacenter/{datacenter_id}/filer/{filer_id}'
                    )
                filer_list.append(
                    discord.OptionChoice(
                        f"🗄️ {filer['name']}",
                        value=f"{datacenter_id}/{filer['filerId']}",
                        )
                    )
        return filer_list