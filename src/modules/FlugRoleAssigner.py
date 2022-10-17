import logging
import time
import discord

import FlugCategories
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
            users: FlugUsers.FlugUsers = None,
            categories: FlugCategories = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users, categories)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))

        
    
    async def get_log_channel_on_ready(self):
        self.logChannel = self.client.get_channel(self.logChannelId)

        if self.logChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the log channel ({self.logChannelId})!")
    
    
    async def process_message(self, message: discord.Message):
        
        # ignore own messages
        if message.author.id == self.client.user.id:
            return

        # ignore messages outside the designated channel
        if not self.channels.isChannelRoleAssignment(str(message.channel.id)):
            return

        # are we allowed to assign a role?
        if self.users.isUserDeactivated(str(message.author.id)):
            logging.warning(
                f"Banned user '{message.author.name}' ({message.author.id}) should not be able to send in {message.channel.name} ({message.channel.id})!"
            )

            await self.logChannel.send(
                f"Banned user '{message.author.name}' ({message.author.id}) should not be able to send in {message.channel.name} ({message.channel.id})!"
            )
            await message.delete()
            return

        # have we entered an existing role name?
        role = discord.utils.get(message.guild.roles, name=message.content)

        embed = discord.Embed(title=f"{self.moduleName}",
                                color=discord.Color.blue())

        if role == None:
            logging.warning(f"Role could not be assigned {message.content}")
            embed.description = f"{message.author.mention} ({message.author.id}) tried to assign the non-existing role '{message.content}'!"
            await message.channel.send(f"Bitte so schreiben wie oben angegeben. {message.author.mention}", delete_after=self.deleteTimer)
            await self.logChannel.send(embed=embed)
            await message.delete()
            return

        # is the role allowed to be assigned?
        if not self.roles.isRoleAssignable(str(role.id)):
            await message.channel.send(f"{message.author.mention}, die Rolle '{role.name}' ist nicht zuteilbar.", delete_after=self.deleteTimer)
            embed.description = f"{message.author.mention} ({message.author.id}) tried to assign non-assignable role '{message.content}'!"
            await self.logChannel.send(embed=embed)
            await message.delete()
            return
        
        # add the role to the author
        await message.author.add_roles(role)

        embed.description = f"Assigned role '{role.name}' to '{message.author.mention}' ({message.author.id})"
        await self.logChannel.send(embed=embed)

        await message.delete()

    def setup(self):
        self.logChannel : discord.Channel = None
        # load the module config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        # get the error message deletion delay
        self.deleteTimer = self.cfg.c().get(DEFAULT_FLUGVOGEL_ROLEADDER_CFG_ERROR_MESSAGE_DELETION_DELAY, None)

        if self.deleteTimer == None:
            logging.critical(f"Config for '{self.moduleName}' doesn't contain '{DEFAULT_FLUGVOGEL_ROLEADDER_CFG_ERROR_MESSAGE_DELETION_DELAY}'!")

            return False

        # fail if no module channel is configured
        self.logChannelId = self.channels.getLogChannelId()

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False

        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)
        self.client.addSubscriber('on_message', self.process_message)

        return True

CLASS = FlugRoleAssigner
