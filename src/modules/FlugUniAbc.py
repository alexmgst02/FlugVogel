import logging

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugCategories
import FlugRoles
import FlugUsers
import FlugConfig
import util.logHelper

FLUGVOGEL_UNIABC_CONFIG_KEY_BASE_URL = "baseUrl"

class FlugUniAbc(modules.FlugModule.FlugModule):
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
        self.logChannelId = self.channels.getLogChannelId()

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False

        # register the event handler to get the log channel
        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)

        # setup the command
        @self.client.tree.command(description="Zeigt einen Verweis auf das Uni-ABC der Freitagsrunde.")
        @discord.app_commands.checks.cooldown(1, 5.0)
        async def uniabc(interaction: discord.Interaction):
            await interaction.response.defer()

            # get the name of the channel
            uniabc_link = self.cfg.c().get(FLUGVOGEL_UNIABC_CONFIG_KEY_BASE_URL, None)

            if uniabc_link == None:
                # unknown channel - respond
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.WARNING, "🚧 Freitagsrunde-Uni-ABC Link nicht konfiguriert! 🚧",
                    f"'{interaction.user.name}' ({interaction.user.mention}) tried to request" +
                    f"the Uni-ABC Link in channel '{interaction.channel.name}' ({interaction.channel.mention}) - NOT CONFIGURED"
                )

                embed = discord.Embed(color=discord.Colour.red(), title="💢 Freitagsrunde-Uni-ABC Link nicht konfiguriert! 💢")
                await interaction.followup.send(embed=embed)

                return

            # build an embed and show the link
            embed = discord.Embed(color=discord.Colour.green(), title="Uni-ABC der Freitagsrunde",
                description=f"{uniabc_link}", type="article"
            )

            await interaction.followup.send(embed=embed)

            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "👍 Successful Uni-ABC Request 👍",
                f"'{interaction.user.name}' ({interaction.user.mention}) requested" +
                f" Uni-ABC Link in the channel '{interaction.channel.name}' ({interaction.channel.mention})"
            )

            return

        return True

CLASS = FlugUniAbc
