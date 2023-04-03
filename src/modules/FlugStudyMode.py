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

DEFAULT_FLUGVOGEL_STUDY_MODE_CFG_ROLE_NAME = "study mode"

class FlugStudyMode(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig
    startupDone: bool = False
    logChannelId: int = None
    logChannel: discord.TextChannel = None
    studyModeRoleId: int = None
    studyModeRole: discord.Role = None

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

    async def get_log_channel_and_role_on_ready(self):
        if self.startupDone:
            return

        self.logChannel = self.client.get_channel(self.logChannelId)

        if self.logChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the log channel ({self.logChannelId})!")

        self.studyModeRole = discord.utils.get(self.client.getGuild().roles, id=self.studyModeRoleId)

        if self.studyModeRole == None:
            logging.critical(f"{self.moduleName} could not load studyModRole.")

        self.startupDone = True

    def setup(self):
        # load the config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        self.logChannelId = self.channels.getChannelId(FlugChannels.DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_LOG)

        if self.logChannelId == None:
            logging.critical(f"{self.moduleName} could not load log channel")
            
            return False

        self.studyModeRoleId = self.roles.getRoleID(DEFAULT_FLUGVOGEL_STUDY_MODE_CFG_ROLE_NAME)

        if self.studyModeRoleId == None:
            logging.critical(f"{self.moduleName} could not load studyModeRole.")

            return False

        # register the event handler to get the log channel
        self.client.addSubscriber('on_ready', self.get_log_channel_and_role_on_ready)

        @self.client.tree.command(description="offtopic kanäle ausblenden")
        @discord.app_commands.checks.cooldown(1, 20.0)
        async def study_mode(interaction: discord.Interaction):
            #check if user wants to leave or enter study mode
            for role in interaction.user.roles:
                if role.id == self.studyModeRoleId:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message("Du hast nun wieder Zugriff auf alle Kanäle.", ephemeral=True)
                    await util.logHelper.logToChannelAndLog(self.logChannel,logging.INFO, f"{self.moduleName}", f"{interaction.user.mention} left study mode.")
                    return
            
            #user wants to enter
            await interaction.response.send_message("Nun sind nurnoch Lernkanäle verfügbar. Um den StudyMode zu verlassen, einfach erneut /study_mode eingeben.", ephemeral=True)
            await interaction.user.add_roles(self.studyModeRole)
            await util.logHelper.logToChannelAndLog(self.logChannel,logging.INFO, f"{self.moduleName}", f"{interaction.user.mention} entered study mode.")

        return True

CLASS = FlugStudyMode
