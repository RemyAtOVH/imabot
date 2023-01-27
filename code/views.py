# -*- coding: utf8 -*-

""" Views declarations. """

import discord

from loguru import logger

from variables import (
    FLAVOR_ID_DATA,
    IMAGE_ID_DATA,
)


class InstanceCreationView(discord.ui.View):
    """ Custom View to display Select dropdowns for Instance creation. """
    def __init__(self, ctx, ovh_client, projectid, sshkeyid):
        super().__init__(timeout=30)
        self.values = {}
        self.ctx = ctx
        self.ovh_client = ovh_client
        self.projectid = projectid
        self.sshkeyid = sshkeyid

    @discord.ui.select(
        placeholder = "Choose the OpenStack region",
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(label="🇫🇷 Gravelines (GRA9)", value="GRA9"),
            discord.SelectOption(label="🇵🇱 Gravelines (WAW1)", value="WAW1"),
            discord.SelectOption(label="🇬🇧 Gravelines (UK1)", value="UK1"),
            discord.SelectOption(label="🇨🇦 Gravelines (BHS1)", value="BHS1"),
        ]
    )
    async def select_callback_region(self, select, interaction):
        """ Callback for region Select """
        self.values['region'] = select.values[0]
        select.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder = "Choose the OpenStack flavor",
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(label="⚙️ Discovery (1vCPU, 2Go RAM)", value="d2-2"),
            discord.SelectOption(label="⚙️ Discovery (2vCPU, 4Go RAM)", value="d2-4"),
            discord.SelectOption(label="⚙️ Discovery (4vCPU, 8Go RAM)", value="d2-8"),
        ]
    )
    async def select_callback_flavor(self, select, interaction):
        """ Callback for flavor Select """
        self.values['flavor'] = select.values[0]
        select.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.select(
        placeholder = "Choose the OpenStack image",
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(label="🐧 Debian 11", value="Debian 11"),
            discord.SelectOption(label="🐧 Ubuntu 22.10", value="Ubuntu 22.10"),
            discord.SelectOption(label="🐧 Fedora 36", value="Fedora 36"),
        ]
    )
    async def select_callback_image(self, select, interaction):
        """ Callback for image Select """
        self.values['image'] = select.values[0]
        select.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        label="Let's go!",
        style=discord.ButtonStyle.green,
        emoji="✅",
        )
    async def button_callback_ok(self, button, interaction):
        """ Callback for OK Button """

        await interaction.response.defer()
        answer = await interaction.followup.send(
            embed=discord.Embed(
                description="The Instance creation will start shortly",
                colour=discord.Colour.green()
                ),
            )

        if any([
            'region' not in self.values,
            'image' not in self.values,
            'flavor' not in self.values,
        ]):
            msg = 'Unable to comply. Missing parameters from Select dropdowns'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await answer.edit(embed=embed)
            return

        try:
            image_id = IMAGE_ID_DATA[self.values['region']][self.values['image']]
            flavor_id = FLAVOR_ID_DATA[self.values['region']][self.values['flavor']]
        except Exception as e:
            msg = f"Unable to comply. Can't find imageId/flavorId [{e}]"
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await answer.edit(embed=embed)
            return

        try:
            res = self.ovh_client.post(
                f'/cloud/project/{self.projectid}/instance',
                flavorId=flavor_id,
                imageId=image_id,
                monthlyBilling=False,
                name="d2-2-imabot",
                region=self.values['region'],
                sshKeyId=self.sshkeyid,
            )
        except Exception as e:
            msg = f'API calls KO (Instance creation) [{e}]'
            logger.error(msg)
            embed = discord.Embed(
                description=msg,
                colour=discord.Colour.red()
            )
            await answer.edit(embed=embed)
            return
        else:
            msg = 'API calls OK (Instance creation)'
            logger.debug(msg)

            embed = discord.Embed(
                title="An Instance is spawning",
                colour=discord.Colour.green()
                )

            embed_field_name = f"[{res['id']}] {res['name']}"
            embed_field_value  = f"> Status : `{res['status']}`\n"
            embed_field_value += f"> Region : `{res['region']}`\n"
            embed_field_value += f"> OS : `{res['flavor']['osType']}`\n"
            embed_field_value += f"> Flavor : `{res['flavor']['name']}`\n"

            embed.add_field(
                name=f'`{embed_field_name}`',
                value=embed_field_value,
                inline=True,
                )
            await answer.edit(embed=embed)
            await self.ctx.delete()