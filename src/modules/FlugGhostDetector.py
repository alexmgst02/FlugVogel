import logging
import datetime
import json

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig

DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD = "threshold"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS = "onlyPings"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_CONFIG_PERMITTED_ROLES = "configPermittedRoles"

DEFAULT_FLUGVOGEL_GHOSTDETECTOR_TRESHOLD = 30
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_ONLYPINGS = False

class FlugGhostDetector(modules.FlugModule.FlugModule):
    logChannel: discord.abc.GuildChannel
    logChannelId: int = None
    onlyPings: bool = None
    treshold: int = None

    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))

    async def get_log_channel_on_ready(self):
        self.logChannel = self.client.get_channel(self.logChannelId)

        if self.logChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the log channel ({self.logChannelId})!")

    async def detect_ghost_on_message_delete(self, message : discord.Message):
        # get the relevant config values
        self.threshold = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD, DEFAULT_FLUGVOGEL_GHOSTDETECTOR_TRESHOLD)
        self.onlyPings = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS, DEFAULT_FLUGVOGEL_GHOSTDETECTOR_ONLYPINGS)

        # check whether the time of deletion is below the threshold
        createdAt = message.created_at
        deletedAt = datetime.datetime.now(datetime.timezone.utc)
        difference = (deletedAt - createdAt).total_seconds()

        if difference > self.threshold and self.threshold != 0:
            return

        # determine whether the message is a reference and whether it's a ping (mention)
        reference = message.reference != None
        ping = len(message.mentions) > 0 or len(message.role_mentions) > 0 or message.mention_everyone
        
        # build the embed which reports the detected ghost reference/ping/message
        embed = discord.Embed(title="👻 Ghost Detector 👻")
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.timestamp = deletedAt

        # references are always mentions/pings; catch both here
        if ping or reference:
            embed.description = f"Possible Ghost-Ping"
            
            if reference:
                embed.description += "/Reference"
        elif not self.onlyPings:
            embed.description = f"Ghost-Message"
        else:
            return

        embed.description += f"\nAuthor: {message.author.mention}\nDeleted after {difference} seconds\nOriginal Message: "

        if len(embed.description) + len(message.content) >= 2000:
            embed.description += "-- Original Message Too Long --"
        else:
            embed.description += message.content

        await self.logChannel.send(embed=embed)

    def setup(self):
        # load the module config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        #roles permitted to config using slash command
        self.permittedRoles = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_CONFIG_PERMITTED_ROLES)

        if self.permittedRoles == None:
            logging.critical(f"Config for '{self.moduleName}' doesn't contain '{DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_CONFIG_PERMITTED_ROLES}'!")

            return False

        # fail if no log channel is configured
        self.logChannelId = self.channels.getLogChannelId()

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False

        #load role ids for slash command config
        self.permittedRoleIds = []
        for key, value in self.roles.roleConfig.c().items():
            if value.get(FlugRoles.DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_NAME) in self.permittedRoles:
                self.permittedRoleIds.append(int(key))
        
        # register the event handlers
        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)
        self.client.addSubscriber('on_message_delete', self.detect_ghost_on_message_delete)

        @self.client.tree.command(description="Configure the FlugGhostDetector")
        @discord.app_commands.describe(
            treshold="Deletion of messages older than the threshold in seconds will be ignored (0 = Infinite).",
            only_pings="Only Register Pings and References",
        )
        async def set_ghost_detector_config(interaction: discord.Interaction, treshold: int, only_pings: bool):
            for role in interaction.user.roles:
                if role.id in self.permittedRoleIds:
                    # save the changes
                    self.cfg._cfgObj.update({DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD:treshold})
                    self.cfg._cfgObj.update({DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS:only_pings})
                    self.cfg.save()

                    # build an embed
                    embed = discord.Embed(title="🚧 New Ghost Detector Config 🚧")
                    embed.description = f"New 'treshold': {treshold}\nNew 'only_pings': {only_pings}"

                    # respond to the user-only and send to the log channel
                    await interaction.response.send_message(
                        f"Set new 'treshold': {treshold} and new 'only_pings': {only_pings}", ephemeral=True
                    )
                    await self.logChannel.send(embed=embed)
    
                    return

            await interaction.response.send_message("Du darfst das nicht nutzen!", ephemeral=True)

        @self.client.tree.command(description="Get the FlugGhostDetector Configuration")
        async def get_ghost_detector_config(interaction: discord.Interaction):
            # build an embed
            for role in interaction.user.roles:
                if role.id in self.permittedRoleIds:
                    embed = discord.Embed(title="🚧 Current Ghost Detector Config 🚧")
                    embed.description = json.dumps(self.cfg.c(), indent=4)

                    await interaction.response.send_message(f"Config sent to {self.logChannel.mention}",ephemeral=True);
                    await self.logChannel.send(embed=embed)

                    return
                    
            await interaction.response.send_message("Du darfst das nicht nutzen!", ephemeral=True)

        return True


CLASS = FlugGhostDetector
