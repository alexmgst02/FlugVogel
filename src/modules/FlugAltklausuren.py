import logging

import discord
import FlugCategories

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig
import util.logHelper

class FlugAltklausuren(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig
    logChannelId: int
    logChannel: discord.TextChannel

    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None,
            categories: FlugCategories.FlugCategories = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users, categories)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))

    async def get_log_channel_on_ready(self):
        self.logChannel = self.client.get_channel(self.logChannelId)

        if self.logChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the log channel ({self.logChannelId})!")

    def setup(self):
        # load the config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        # fail if no log channel is configured
        self.logChannelId = self.channels.getChannelId(FlugChannels.DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_LOG)

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False

        # register the event handler to get the log channel
        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)

        # setup the command
        @self.client.tree.command(description="Zeigt einen Verweis zu den Freitagsrunde-Altklausuren (...) zum Modul des aktuellen Kanals.")
        @discord.app_commands.checks.cooldown(1, 10.0)
        async def altklausuren(interaction: discord.Interaction):
            await interaction.response.defer()

            # get the name of the channel
            name = self.channels.getChannelName(str(interaction.channel.id))

            if name == None:
                # unknown channel - respond
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.WARNING, "🚧 Invalid Altklausuren Request 🚧",
                    f"'{interaction.user.name}' ({interaction.user.mention}) tried to request" +
                    f"Altklausuren in the unknown channel '{interaction.channel.name}' ({interaction.channel.mention})"
                )

                embed = discord.Embed(color=discord.Colour.red(), title="💢 Für diesen Kanal ist kein Altklausurenverweis konfiguriert! 💢")
                await interaction.followup.send(embed=embed)

                return

            # go through the config and check whether the channel is found
            key: str

            for key, v in self.cfg.c().items():
                if type(key) != str:
                    continue

                if key.lower() == name.lower():
                    embed = discord.Embed(color=discord.Colour.green(), title="🔗 Altklausurenverweis 🔗", type="link")
                    embed.description = v

                    await interaction.followup.send(embed=embed)

                    await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "👍 Successful Altklausuren Request 👍",
                        f"'{interaction.user.name}' ({interaction.user.mention}) requested" +
                        f" Altklausuren in the channel '{interaction.channel.name}' ({interaction.channel.mention})"
                    )

                    return

            # no link found
            await util.logHelper.logToChannelAndLog(self.logChannel, logging.WARNING, "🚧 Invalid Altklausuren Request 🚧",
                f"'{interaction.user.name}' ({interaction.user.mention}) tried to request" +
                f"Altklausuren in a channel without a Altklausurenlink: '{interaction.channel.name}' ({interaction.channel.mention})"
            )

            embed = discord.Embed(color=discord.Colour.red(), title="💢 Für diesen Kanal ist kein Altklausurenverweis konfiguriert! 💢")
            await interaction.followup.send(embed=embed)

            return

        return True

CLASS = FlugAltklausuren
