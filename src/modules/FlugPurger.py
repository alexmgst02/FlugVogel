import asyncio
import logging
import typing
import datetime

import discord

import util.flugTextLength
import util.flugVoterHelper
import util.flugPermissionsHelper
import util.logHelper

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugCategories
import FlugRoles
import FlugUsers
import FlugConfig
import FlugPermissions

DEFAULT_FLUGVOGEL_USER_PURGE_CFG_PERMISSIONS = "permissions"
DEFAULT_FLUGVOGEL_USER_PURGE_CFG_PERMISSIONS_PURGE = "purge"

class FlugPurger(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig
    logChannelId: int
    logChannel: discord.TextChannel
    permissions: FlugPermissions.FlugPermissions = None

    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None,
            users: FlugUsers.FlugUsers = None,
            categories: FlugCategories.FlugCategories = None):
        # set up the super class
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

        # initialize the permission config
        try:
            self.permissions = FlugPermissions.FlugPermissions(
                self.cfg.c().get(DEFAULT_FLUGVOGEL_USER_PURGE_CFG_PERMISSIONS),
                self.roles, self.users
            )
        except Exception as e:
            logging.critical(f"Failed to setup permission config for {self.moduleName}!")
            logging.exception(e)

            return False

        # fail if no log channel is configured
        self.logChannelId = self.channels.getChannelId(FlugChannels.DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_LOG)

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False

        # register the event handler to get the log channel
        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)

        # slash command to purge a specified amount of messages
        @self.client.tree.command(description="purge messages")
        @discord.app_commands.describe(member="user of whom to delete messages (optional)",
                                       limit="how many messages are to be deleted",
                                       search_limit="amount of msg to search through if user specified - defaults to limit+100, enter 0 for no limit (slow)",
                                       reason="why purge the shit out of them")
        async def purge(interaction: discord.Interaction, limit: int, search_limit: int=100, reason: str="default", member: discord.Member=None):
            await interaction.response.defer(ephemeral=True)
            if not await util.flugPermissionsHelper.canDoWrapper(DEFAULT_FLUGVOGEL_USER_PURGE_CFG_PERMISSIONS_PURGE,
                                                                 interaction.user, member, self.permissions, self.logChannel):
                await interaction.followup.send("Die Nutzung dieses Befehls ist für Sie untersagt! Dieser Vorfall wird gemeldet 🚔!", ephemeral=True)
                return

            if limit <= 0:
                await interaction.followup.send("Bitte eine Zahl größer Null eingeben!", ephemeral=True)
                return

            if not member:
                await interaction.channel.purge(limit=limit)
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "Purge", f"{interaction.user.mention} deleted {limit} messages in {interaction.channel.mention}.\nreason: {reason}.")  # in channel: <...> is missing currently
                return await interaction.followup.send(f"Es wurden die letzen {limit} Nachrichten gelöscht.")

            #search_limit = amount of messages to grab from channel history
            if search_limit == 0: 
                search_limit=None
            else:
                search_limit += limit

            #only delete messages from member
            msg = []
            deleted = 0
            now = datetime.datetime.now(datetime.timezone.utc)
            twoWeeksAgo = now - datetime.timedelta(days=14)
            async for m in interaction.channel.history(limit=search_limit, after=twoWeeksAgo, oldest_first=False):
                if deleted == limit:
                    break

                if m.author == member:
                    msg.append(m)
                    deleted += 1

                if len(msg) >= 100:
                    await interaction.channel.delete_messages(msg)        
                    msg = []

            if len(msg) > 0:
                await interaction.channel.delete_messages(msg)

            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "Purge", f"{interaction.user.mention} deleted {deleted} messages from {member} in {interaction.channel.mention}. {search_limit} messages were looked at (None means entire channel history)\nreason: {reason}.")

            return await interaction.followup.send(f"Es wurden {deleted} Nachrichten von {member} gelöscht.")

        return True


CLASS = FlugPurger
