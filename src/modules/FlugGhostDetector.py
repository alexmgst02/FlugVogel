import logging
import time
import discord
import datetime

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig

DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD = "threshold"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS = "onlyPings"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_CONFIG_PERMITTED_ROLES = "configPermittedRoles"

class FlugGhostDetector(modules.FlugModule.FlugModule):
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
            logging.critical(f"'{self.moduleName}' could not find the log channel ({logChannelId})!")
    
    
    async def detect_ghost_on_message_delete(self, message : discord.Message):
        self.threshold = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD, None)
        self.onlyPings = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS)

        ping = False
        reference = False
        createdAt = message.created_at
        deletedAt = datetime.datetime.now(datetime.timezone.utc)
        difference = (deletedAt-createdAt).total_seconds()
        if  difference <= self.threshold:
            if message.reference != None:
                reference = True
            if (len(message.mentions) > 0) or (len(message.role_mentions) > 0) or message.mention_everyone :
                ping = True
                
            embed = discord.Embed(title=f"GhostDetector")
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.timestamp = deletedAt

            if ping or reference:
                embed.description = f"Possible ghostping. Referenced other message: {reference}\n Content: '{message.content}'\n Author: {message.author.mention}\n Deleted After {difference} seconds"
            elif not self.onlyPings:
                embed.description = f"Ghostmessage.\n Content: '{message.content}'\n Author: {message.author.mention}\n Deleted after {difference} seconds."
            else:
                return
            
            if len(embed.description) >= 2000:
                embed.description = f"Original message too long to show. Ping: {ping}, reference: {reference}\n Author: {message.author.mention}\n Deleted after: {difference} seconds.."
            await self.logChannel.send(embed=embed)    
    def setup(self):
        self.threshold : int = None
        self.onlyPings : bool = None
        self.logChannel : discord.Channel = None
        # load the module config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        self.threshold = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD, None)
    
        if self.threshold == None:
            logging.critical(f"Config for '{self.moduleName}' doesn't contain '{DEFAULT_FLUGVOGEL_GHOSTDETECTER_CFG_THRESHOLD}'!")

            return False

        self.onlyPings = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS)

        if self.onlyPings == None:
            logging.critical(f"Config for '{self.moduleName}' doesn't contain '{DEFAULT_FLUGVOGEL_GHOSTDETECTER_CFG_ONLY_PINGS}'!")

            return False

        #roles permitted to config using slash command
        self.permittedRoles = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_CONFIG_PERMITTED_ROLES)

        if self.permittedRoles == None:
            logging.critical(f"Config for '{self.moduleName}' doesn't contain '{DEFAULT_FLUGVOGEL_GHOSTDETECTER_CFG_CONFIG_PERMITTED_ROLES}'!")

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
        

        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)
        self.client.addSubscriber('on_message_delete', self.detect_ghost_on_message_delete)

        @self.client.tree.command()
        @discord.app_commands.describe(
            first_value="Threshold",
            second_value="only register pings",
        )
        async def configghostdetector(interaction: discord.Interaction, first_value: int, second_value: bool):
            for role in interaction.user.roles:
                if role.id in self.permittedRoleIds:
                    msg = f"Setting Threshold to {first_value}, onlyPings to {second_value}"
                    await interaction.response.send_message(msg, ephemeral=True)
                    await self.logChannel.send(f"GhostDetectorConfig: {msg}")
                    self.cfg._cfgObj.update({DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD:first_value})
                    self.cfg._cfgObj.update({DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS:second_value})
                    self.cfg.save()
                    return


    
                    return
            await interaction.response.send_message(f"Du darfst das nicht nutzen!", ephemeral=True)


        return True

CLASS = FlugGhostDetector
