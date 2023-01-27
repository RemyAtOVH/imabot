"""
Discord ommand definition for:
/{DISCORD_GROUP_GENERAL} settings
"""
import os

import discord
import ovh

from loguru import logger

# OVHcloud API credentials
# You can generate them here: https://api.ovh.com/createToken/
# DO NOT HARDCODE THEM HERE !
# They are meant to be passed as ENV vars (secrets) to ensure your safety.
OVH_ENDPOINT = os.environ.get("OVH_ENDPOINT", 'ovh-eu')
OVH_AK = os.environ.get("OVH_APPLICATION_KEY")
OVH_AS = os.environ.get("OVH_APPLICATION_SECRET")
OVH_CK = os.environ.get("OVH_CONSUMER_KEY")

DISCORD_GROUP_GENERAL = os.environ.get("DISCORD_GROUP_GENERAL", 'iamabot')
ROLE_ACCOUNTING = os.environ.get("DISCORD_ROLE_ACCOUNTING", "Accounting")

def settings(group_global):
    @group_global.command(
        description='Command to display Bot settings (API keys, roles, ...)',
        default_permission=False,
        name='settings',
        )
    async def settings(
        ctx,
    ):
        """This part performs checks and display info on bot config."""
        # As we rely on potentially a lot of API calls, we need time to answer
        await ctx.defer()
        # Pre-flight checks
        if ctx.channel.type is discord.ChannelType.private:
            channel = ctx.channel.type
        else:
            channel = ctx.channel.name
        name = ctx.author.name
        logger.info(f'[#{channel}][{name}] /settings')

        embed = discord.Embed(
                title='**Bot settings**',
                colour=discord.Colour.blue()
                )

        try:
            # Lets check OVHcloud API credentials
            if any([
                OVH_ENDPOINT is None,
                OVH_AK is None,
                OVH_AS is None,
                OVH_CK is None,
            ]):
                # At least one of the credentials info is missing
                value_credentials=(
                    ':warning: '
                    'One of your OVHcloud API credentials is missing.\n'
                    'Check your ENV vars!'
                    )
        except Exception as e:
            msg = f'Credentials loading KO [{e}]'
            logger.error(msg)
            value_credentials=f':no_entry: {e}'
        else:
            # Everything is OK
            value_credentials = (
                ':white_check_mark: '
                'Your OVHcloud API credentials are set up!'
                )
        embed.add_field(
            name='Credentials',
            value=value_credentials,
            inline=False,
            )

        try:
            # Lets check OVHcloud API connection status
            ovh_client = ovh.Client(
                endpoint=OVH_ENDPOINT,
                application_key=OVH_AK,
                application_secret=OVH_AS,
                consumer_key=OVH_CK,
                )
            me = ovh_client.get('/me')
            # At least one of the credentials info is missing
            if me is None or me['nichandle'] is None:
                value_auth=(
                    ':warning: '
                    'Authentication to OVHcloud API failed.\n'
                    'Check the validity of your credentials!'
                    )
        except Exception as e:
            msg = f'OVHcloud API calls KO [{e}]'
            logger.error(msg)
            value_auth=f':no_entry: {e}'
        else:
            # Everything is OK
            value_auth = (
                ':white_check_mark: '
                "Authentication to OVHcloud API successfull! "
                f"(**{me['nichandle']}**)"
                )
        embed.add_field(
            name='Authentication',
            value=value_auth,
            inline=False,
            )

        try:
            # We answer
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