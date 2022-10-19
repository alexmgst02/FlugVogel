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
import FlugPermissions

import util.flugPermissionsHelper
import util.logHelper

DEFAULT_FLUGVOGEL_ROLEADDER_CFG_ERROR_MESSAGE_DELETION_DELAY = "errorMessageDeletionDelay"
DEFAULT_FLUGVOGEL_ROLE_ASSIGNER_CFG_PERMISSIONS = "permissions"

class FlugRoleAssigner(modules.FlugModule.FlugModule):
    permissions: FlugPermissions.FlugPermissions = None

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

        # initialize the permission config
        try:
            self.permissions = FlugPermissions.FlugPermissions(
                self.cfg.c().get(DEFAULT_FLUGVOGEL_ROLE_ASSIGNER_CFG_PERMISSIONS),
                self.roles, self.users
            )
        except Exception as e:
            logging.critical(f"Failed to setup permission config for {self.moduleName}!")
            logging.exception(e)

            return False


        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)
        self.client.addSubscriber('on_message', self.process_message)

        @self.client.tree.command(description="Neue Studiengangsrolle wählen")
        @discord.app_commands.describe(
            name="Name der Studiengangsrolle"

        )
        async def neue_rolle(interaction: discord.Interaction, name: str):
            if not await util.flugPermissionsHelper.canDoWrapper("assignRoleCommand", interaction.user, None, self.permissions, self.logChannel):
                return

            if self.users.isUserDeactivated(str(interaction.user.id)):
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.WARNING, "Flug RoleAssigner Warning", f"Banned user '{interaction.user.mention}' should not be able to use /neue_rolle." )
                return

            role = discord.utils.get(interaction.guild.roles, name=name)
             
            if role == None:
                await interaction.response.send_message(f"Die Rolle {name} existiert nicht.", ephemeral=True)
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "Invalid Role Request", f"{interaction.user.mention} tried to assign non-existent role '{name}' using /neue_rolle.")
                return

            if not self.roles.isRoleAssignable(str(role.id)):
                await interaction.response.send_message(f"Die Rolle {name} ist nicht zuweisbar.", ephemeral=True)
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "Invalid Role Request", f"{interaction.user.mention} tried to assign non-assignable role '{name}' using /neue_rolle.")
                return

            for tmpRole in interaction.user.roles:
                if tmpRole.is_assignable() and self.roles.isRoleAssignable(str(tmpRole.id)): #remove studiengangsrollen
                    await interaction.user.remove_roles(tmpRole)

            await interaction.user.add_roles(role)

            await interaction.response.send_message(f"Die Rolle {role.name} wurde erfolgreich zugeteilt", ephemeral=True)
            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "Assigned Role", f"{interaction.user.mention} self-assigned Role '{role.name}'.")

        return True

CLASS = FlugRoleAssigner
