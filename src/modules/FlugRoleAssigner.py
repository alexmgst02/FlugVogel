import logging
import time
import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig

DEFAULT_FLUGVOGEL_ROLEADDER_CFG_ERROR_MESSAGE_DELETION_DELAY = "errorMessageDeletionDelay"

class FlugRoleAssigner(modules.FlugModule.FlugModule):
    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))

    def setup(self):
        # load the module config
        cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        # get the error message deletion delay
        deleteTimer = cfg.c().get(DEFAULT_FLUGVOGEL_ROLEADDER_CFG_ERROR_MESSAGE_DELETION_DELAY, None)

        if deleteTimer == None:
            logging.critical(f"Config for '{self.moduleName}' doesn't contain '{DEFAULT_FLUGVOGEL_ROLEADDER_CFG_ERROR_MESSAGE_DELETION_DELAY}'!")

            return False

        # fail if no module channel is configured
        logChannelId = self.channels.getLogChannelId()

        if logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False
        
        @self.client.subscribeTo('on_ready')
        async def get_log_channel_on_ready():
            logChannel = self.client.get_channel(int(logChannelId))

            if logChannel == None:
                logging.critical(f"'{self.moduleName}' could not find the log channel ({logChannelId})!")
        
        @self.client.subscribeTo('on_message')
        async def proccess_message(message: discord.Message):
            logChannel = self.client.get_channel(int(logChannelId))
            
            # ignore own messages
            if message.author.id == self.client.user.id:
                return

            # ignore messages outside the designated channel
            if not self.channels.isChannelRoleAssignment(str(message.channel.id)):
                return

            # are we allowed to assign a role?
            if self.users.isUserDeactivated(message.author.id):
                logging.warning(
                    f"Banned user '{message.author.name}' ({message.author.id}) should not be able to send in {message.channel.name} ({message.channel.id})!"
                )

                await logChannel.send(
                    f"Banned user '{message.author.name}' ({message.author.id}) should not be able to send in {message.channel.name} ({message.channel.id})!"
                )
                await message.delete()
                return

            # have we entered an existing role name?
            role = discord.utils.get(message.guild.roles, name=message.content)

            if role == None:
                logging.warning(f"Role could not be assigned {message.content}")

                await message.channel.send(f"Bitte so schreiben wie oben angegeben. {message.author.mention}", delete_after=deleteTimer)
                await logChannel.send(f"{message.author.mention} ({message.author.id}) tried to assign the non-assignable role '{message.content}'!")
                await message.delete()
                return

            # is the role allowed to be assigned?
            if not self.roles.isRoleAssignable(str(role.id)):
                await message.channel.send(f"{message.author.mention}, die Rolle '{role.name}' ist nicht zuteilbar.", delete_after=deleteTimer)
                await message.delete()
                return
            
            # add the role to the author
            await message.author.add_roles(role)

            await logChannel.send(f"Assigned role '{role.name}' to '{message.author.mention}' ({message.author.id})")

            await message.delete()

        return True

CLASS = FlugRoleAssigner
