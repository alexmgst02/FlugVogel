import logging

import discord
from discord.ext import tasks

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugCategories
import FlugRoles
import FlugUsers
import FlugConfig

import util.logHelper

DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_PRIOR_COUNT = "priorMemberCount"

class FlugStatistics(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig
    logChannelId: int
    logChannel: discord.TextChannel
    guild: discord.Guild
    memberCountChannelId: int = None
    memberCountChannel: discord.VoiceChannel = None    
    priorMemberCount: int  = None

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

    async def get_guild_and_log_on_ready(self):
        self.guild = self.client.getGuild()

        self.logChannel = self.client.get_channel(self.logChannelId)
        self.memberCountChannel = self.client.get_channel(self.memberCountChannelId)

        #start backlground loop
        if not self.statistics.is_running():
            self.statistics.start()


    def setup(self):
        # load the config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")


        self.memberCountChannelId = self.channels.getMemberCountChannelId()

        if self.memberCountChannelId == None:
            logging.critical(f"No ID found for member count channel. {self.moduleName}")

            return False

        self.priorMemberCount = self.cfg.c().get(DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_PRIOR_COUNT)

        if self.priorMemberCount == None:
            self.priorMemberCount = 0

        # fail if no log channel is configured
        self.logChannelId = self.channels.getLogChannelId()

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False

        # register the event handler to get the log channel
        self.client.addSubscriber('on_ready', self.get_guild_and_log_on_ready)
        
        return True
    
    @tasks.loop(minutes=3)
    async def statistics(self):
        members = self.guild.member_count

        if members > self.priorMemberCount:
            #update the counter
            await self.memberCountChannel.edit(name=f"Total Members: {members}")

            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "FlugStatistics", f"Updated member count from {self.priorMemberCount} to {members}.")

            #save new member counter
            self.priorMemberCount = members
            self.cfg._cfgObj.update({DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_PRIOR_COUNT:self.priorMemberCount})
            self.cfg.save()


CLASS = FlugStatistics