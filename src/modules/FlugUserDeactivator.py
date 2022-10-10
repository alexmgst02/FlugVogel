import logging

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig
import FlugPermissions

import util.flugPermissionsHelper

DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_CFG_PERMISSIONS = "permissions"

DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_CFG_PERMISSIONS_DEACTIVATE_USER = "deactivate_user"


class FlugUserDeactivator(modules.FlugModule.FlugModule):
    logChannel: discord.abc.GuildChannel
    logChannelId: int = None
    deactivationRoleId : int = None
    permissions : FlugPermissions.FlugPermissions = None

    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))


    async def on_ready(self):
        self.logChannel = self.client.get_channel(self.logChannelId)

        if self.logChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the log channel ({self.logChannelId})!")

    
    #checks if the user has been deactivated and reapplies the configured role
    async def member_join(self, member : discord.Member):

        if self.users.isUserDeactivated(str(member.id)):
            for role in member.roles:
                if role.is_assignable():
                    await member.remove_roles(role)

            await member.add_roles(discord.utils.get(member.guild.roles, id=self.deactivationRoleId))

            embed = discord.Embed(title="⚰️User has been deactivated after rejoin⚰️",
                                  color=discord.Colour.green())
            embed.description = f"{member.mention} has been deactivated on rejoin."
            await self.logChannel.send(embed=embed)

    def setup(self):
        # load the module config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        # initialize the permission config
        try:
            self.permissions = FlugPermissions.FlugPermissions(
                self.cfg.c().get(DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_CFG_PERMISSIONS),
                self.roles, self.users
            )
        except Exception as e:
            logging.critical(f"Failed to setup permission config for {self.moduleName}!")
            logging.exception(e)

            return False
        # fail if no log channel is configured
        self.logChannelId = self.channels.getLogChannelId()

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False

        #get the role
        self.deactivationRoleId = self.roles.getDeactivationRole();
        if self.deactivationRoleId == None:
            logging.critical(f"{self.moduleName} could not load deactivationRoleId")
            return False

        
        # register the event handlers
        self.client.addSubscriber('on_ready', self.on_ready)
        self.client.addSubscriber('on_member_join', self.member_join)
        #Slash Command to deactivate member
        @self.client.tree.command(description="Deactivate a user")
        @discord.app_commands.describe(
            member="Member to deactivate",
            reason="Why should the member be deactivated"
        )
        async def deactivate(interaction : discord.Interaction, member : discord.Member, reason : str):

            if not await util.flugPermissionsHelper.canDoWrapper(DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_CFG_PERMISSIONS_DEACTIVATE_USER, interaction.user, member, self.permissions, self.logChannel):
                await interaction.response.send_message("Die Nutzung dieses Befehls ist für Sie untersagt! Dieser Vorfall wird gemeldet 🚔!", ephemeral=True)
                return
            
            #update the config entry
            entry = self.users.userConfig.c().get(str(member.id))
            if entry == None:
                entry = {}
                        
            entry.update({FlugRoles.DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_DEACTIVATED:True})
            self.users.userConfig.c().update({str(member.id):entry})
            self.users.save()
                    
            #remove all roles
            for role in member.roles:
                if role.is_assignable():
                    await member.remove_roles(role)

            #assign ban role
            await member.add_roles(discord.utils.get(interaction.guild.roles, id=self.deactivationRoleId))

                    
            embed = discord.Embed(title="⚰️User has been deactivated⚰️",
                                            color=discord.Colour.green())
            embed.description = f"{interaction.user.mention} deactivated {member.mention} for the following reason:\n{reason}"
            await self.logChannel.send(embed=embed)
            await interaction.response.send_message(f"See {self.logChannel.mention}", ephemeral=True)
                    
            return

        return True


CLASS = FlugUserDeactivator
