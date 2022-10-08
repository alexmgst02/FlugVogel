import logging

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig


class FlugMessageReporter(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig = None
    reportChannelId: int = None
    reportChannel: discord.abc.GuildChannel = None

    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))
        
    async def get_report_channel_on_ready(self):
        self.reportChannel = self.client.get_channel(self.reportChannelId)

        if self.reportChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the report channel ({self.reportChannelId})!")

    def setup(self):
        # load the module config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")
            
        # fail if no report channel is configured
        self.reportChannelId = self.channels.getReportChannelId()

        if self.reportChannelId == None:
            logging.critical(f"No ID found for the Report-Channel '{self.moduleName}'!")

            return False

        # register self.get_report_channel_on_ready for on_ready
        self.client.addSubscriber("on_ready", self.get_report_channel_on_ready)

        # register the context menu to report a message
        @self.client.tree.context_menu(name="Nachricht melden")
        async def report_message(interaction: discord.Interaction, message: discord.Message):
            # We're sending this response message with ephemeral=True, so only the command executor can see it
            await interaction.response.send_message(
                f"Danke für das Melden der Nachricht von {message.author.mention}, die Moderatoren werden zeitnah reagieren.", ephemeral=True
            )

            # Handle report by sending it into the report channels
            embed = discord.Embed(
                title=f"{interaction.user.display_name} ({interaction.user.id}) reported message",
                color = discord.Color.dark_red()
            )
            
            if message.content:
                embed.description = message.content

            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.timestamp = message.created_at

            # create a button linking to the reported message
            url_view = discord.ui.View()
            url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))

            await self.reportChannel.send(embed=embed, view=url_view)
        
        return True

CLASS = FlugMessageReporter
