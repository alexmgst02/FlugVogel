import logging

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig

DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_PERMITTED_ROLES = "permittedRoles"
DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_WHITELISTED_ROLES = "theUntouchableRoles"

class FlugUserDeactivator(modules.FlugModule.FlugModule):
    logChannel: discord.abc.GuildChannel
    logChannelId: int = None
    permittedRoles   = None
    permittedRoleIds  = None
    whitelistedRoles = None
    whitelistedRoleIds  = None
    deactivationRoleId : int = None

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

        #roles permitted to use slash command
        self.permittedRoles = self.cfg.c().get(DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_PERMITTED_ROLES)

        if self.permittedRoles == None:
            logging.critical(f"Config for '{self.moduleName}' doesn't contain '{DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_PERMITTED_ROLES}'!")
            
            return False            

        self.whitelistedRoles = self.cfg.c().get(DEFAULT_FLUGVOGEL_USER_DEACTIVATOR_WHITELISTED_ROLES);

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
        

        #load permitted role ids for slash command 
        self.permittedRoleIds = []
        self.whitelistedRoleIds = []
        for key, value in self.roles.roleConfig.c().items():
            name = value.get(FlugRoles.DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_NAME) 
            if  name in self.permittedRoles:
                self.permittedRoleIds.append(int(key))
            if name in self.whitelistedRoles:
                self.whitelistedRoleIds.append(int(key))

        #load whitelisted role ids for slash command
        
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
            for role in interaction.user.roles:
                if role.id in self.permittedRoleIds:

                    #check if user is whitelisted
                    for role in member.roles:
                        if role.id in self.whitelistedRoleIds:
                            await interaction.response.send_message(f"'{role.name}' is whitelisted!",ephemeral=True)
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

            await interaction.response.send_message("Du darfst das nicht nutzen!", ephemeral=True)


        return True


CLASS = FlugUserDeactivator
