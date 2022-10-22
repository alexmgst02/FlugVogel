import logging
import asyncio

import discord
from discord.ext import commands

import FlugPermissions

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugCategories
import FlugRoles
import FlugUsers
import FlugConfig

import util.logHelper
import util.flugPermissionsHelper

DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_CATEGORYID = "ticketCategoryId"
DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_OLD_TICKET_MESSAGEID = "ticketMessageId"
DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_MAX_CLOSED_ACTIVE_TICKETS = "maxClosedTickets"
DEFAULT_FLUGVOGEL_TICKETS_CFG_PERMISSIONS = "permissions"
DEFAULT_FLUGVOGEL_TICKETS_CFG_PERMISSION_MANAGE_TICKETS = "manage_tickets"

class CancelButton(discord.ui.Button):
    guild : discord.Guild = None
    originalInteraction : discord.Interaction

    def __init__(self, guild : discord.Guild, interaction : discord.Interaction):
        super().__init__(label="Abbrechen", style=discord.ButtonStyle.green)
        self.guild = guild
        self.originalInteraction = interaction

    async def callback(self, interaction: discord.Interaction):
        await self.originalInteraction.delete_original_response()



class CancelTicketButton(discord.ui.Button):
    guild : discord.Guild = None
    logChannel : discord.TextChannel = None    
    ticketChannel : discord.CategoryChannel = None
    ticketCreator : discord.Member = None
    originalInteraction : discord.Interaction = None
    permissions : FlugPermissions.FlugPermissions = None

    def __init__(self, guild : discord.Guild, ticketChannel : discord.TextChannel, logChannel : discord.TextChannel, ticketCreator : discord.Member, originalInteraction : discord.Interaction, permissions : FlugPermissions.FlugPermissions):
        super().__init__(label="🔒Bestätigen🔒", style=discord.ButtonStyle.red)
        self.ticketChannel = ticketChannel
        self.guild = guild
        self.logChannel = logChannel
        self.ticketCreator = ticketCreator
        self.originalInteraction = originalInteraction
        self.permissions = permissions

    async def callback(self, interaction : discord.Interaction):
        await interaction.response.defer()

        #Users with the 'manage_tickets' permission will delete the ticket channel - other users will simply deactivate the ticket and leave the channel open to moderators
        if self.permissions.canDo(DEFAULT_FLUGVOGEL_TICKETS_CFG_PERMISSION_MANAGE_TICKETS, interaction.user, None) < FlugPermissions.FlugPermissions.CAN_DO_WEAK_YES:
            #revoke permissions for ticket creator
            await self.ticketChannel.set_permissions(self.ticketCreator, read_messages=False, send_messages=False)
            
            #count amount of closed tickets of ticket owner
            max = 1
            for channel in self.ticketChannel.category.text_channels:
                channelName = channel.name
                channelParts = channelName.split("-")
                if len(channelParts) < 4:
                    continue

                userId = int(channelParts[1])

                if userId != interaction.user.id:
                    continue

                ticketCount = int(channelParts[3])
                if ticketCount > max:
                    max = ticketCount
                elif ticketCount == max:
                    max += 1
            
            #rename the channel
            newName =  f"ticket-{interaction.user.id}-closed-{max}"
            await self.ticketChannel.edit(name=newName)


            await interaction.followup.send(f"closed ticket for {interaction.user.mention}")
            await self.originalInteraction.delete_original_response()
            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "FlugTickets", f"{interaction.user.mention} closed ticket by {self.ticketCreator.mention}  - it remains open to moderators.")
            
        else:
            await interaction.followup.send("closed ticket, deleting channel.")
            await asyncio.sleep(1)
            await self.ticketChannel.delete()
            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "FlugTickets", f"{interaction.user.mention} closed ticket by {self.ticketCreator.mention} - channel has been deleted.")



#Button attached to ticket menu 
class TicketButton(discord.ui.Button):
    guild : discord.Guild = None
    logChannel : discord.TextChannel = None    
    ticketChannel : discord.TextChannel = None
    ticketCreator : discord.Member = None
    permissions : FlugPermissions.FlugPermissions = None
    cooldown : commands.CooldownMapping = None

    def __init__(self, guild : discord.Guild, ticketChannel : discord.TextChannel, logChannel : discord.TextChannel, ticketCreator : discord.Member, permissions : FlugPermissions.FlugPermissions):
        super().__init__(label="🔒Ticket schließen", style=discord.ButtonStyle.gray)
        self.ticketChannel = ticketChannel
        self.guild = guild
        self.logChannel = logChannel
        self.ticketCreator = ticketCreator
        self.permissions = permissions
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 10.0, commands.BucketType.member)

   
    async def callback(self, interaction : discord.Interaction):
        retry = self.cooldown.get_bucket(interaction.message).update_rate_limit()
        #Check cooldown
        if retry:
            await interaction.response.send_message(f"Nicht so schnell. Versuche es in {retry} Sekunden erneut. ", ephemeral=True)
            return

        view = discord.ui.View(timeout=None)
        closeBtn = CancelTicketButton(self.guild, self.ticketChannel, self.logChannel, self.ticketCreator, interaction, self.permissions)
        cancelButton = CancelButton(self.guild, interaction)
        view.add_item(closeBtn)
        view.add_item(cancelButton)
        await interaction.response.send_message(f"Sicher, {interaction.user.mention}?", view=view)


#button attached to ticket create menu
class CreateTicketButton(discord.ui.Button):
    guild : discord.Guild = None
    logChannel : discord.TextChannel = None
    maxClosed : int = None
    ticketCategory : discord.CategoryChannel = None
    permissions : FlugPermissions.FlugPermissions

    def __init__(self, guild : discord.Guild, ticketCategory : discord.CategoryChannel, logChannel : discord.TextChannel, maxClosed : int, permissions :FlugPermissions.FlugPermissions):
        super().__init__(label="📩 Ticket erstellen", style=discord.ButtonStyle.gray)
        self.ticketCategory = ticketCategory
        self.guild = guild
        self.logChannel = logChannel
        self.maxClosed = maxClosed
        self.permissions = permissions

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ticketChannelName = f"ticket-{interaction.user.id}" #must be unique
        

        #check if user already has an open ticket. otherwise create new ticket.
        existingChannel = discord.utils.get(self.guild.text_channels, name=ticketChannelName)
        if existingChannel != None:
            await interaction.followup.send(f"Es existiert bereits das Ticket {existingChannel.mention}. Dieser Vorfall wird gemeldet🚔!", ephemeral=True)
            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "📩FlugTickets📩", f"{interaction.user.mention} tried to open second ticket.")

            return

        #check if user has more closed (but still existing) tickets than allowed
        ticketCount = 0
        for channel in self.ticketCategory.text_channels:
            channelName = channel.name
            channelParts = channelName.split("-")
            if len(channelParts) < 4:
                continue

            userId = int(channelParts[1])

            if userId != interaction.user.id:
                continue

            ticketCount += 1

            if ticketCount >= self.maxClosed:
                await interaction.followup.send(f"Es existieren noch {ticketCount} geschlossene Tickets, welche noch verarbeitet werden. Dieser Vorfall wird gemeldet🚔!", ephemeral=True)
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "📩FlugTickets📩", f"{interaction.user.mention} tried to open {ticketCount+1}. ticket.")

                return                
            
        
        #create channel first - it syncs perms with the catgory
        newChannel = await self.ticketCategory.create_text_channel(ticketChannelName)
    
        #get member to set perms
        member = self.guild.get_member(interaction.user.id)

        #update perms
        await newChannel.set_permissions(member, read_messages=True, send_messages=True)

        await interaction.followup.send(f"Ticket erstellt: {newChannel.mention}", ephemeral=True)

        #setup ticket view and embed
        view = discord.ui.View(timeout=None)
        ticketButton = TicketButton(self.guild, newChannel, self.logChannel, member, self.permissions)
        view.add_item(ticketButton)

        ticketEmbed = discord.Embed(color=discord.Color.green())
        ticketEmbed.title = f"Support Ticket"
        ticketEmbed.description = ("Das Ticket wurde Erfolgreich erstellt. Sie können bereits Ihr Anliegen beschreiben, ein Moderator wird sich Ihnen zeitnah zuwenden.\n" +
                                   "Sobald die Angelegenheit Ihrerseits geklärt ist können Sie 'Ticket schließen' drücken. Damit wird der Ticket-Kanal für Sie unsichtbar und zeitnah von den Moderatoren gelöscht.")


        await newChannel.send(embed=ticketEmbed, view=view)


        await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "📩FlugTickets📩", f"{interaction.user.mention} opened ticket.")

        

class FlugTickets(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig
    logChannelId : int = None
    logChannel : discord.TextChannel = None
    ticketChannelId : int = None
    ticketChannel : discord.TextChannel = None
    startupDone : bool = False
    ticketCategoryId : int = None
    ticketCategory : discord.CategoryChannel = None
    guild : discord.Guild = None
    maxClosedTickets : int = None
    permissions : FlugPermissions.FlugPermissions = None

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


    async def setup_tickets_on_startup(self):
        #setup the ticket embed and view in the main ticket channel
        if not self.startupDone:            

            ticketChannelEmbed = discord.Embed(color=discord.Color.green())
            ticketChannelEmbed.set_author(name=self.client.user.name, icon_url=self.client.user.display_avatar.url) 
            ticketChannelEmbed.title = "Moderatoren kontaktieren"
            ticketChannelEmbed.description = f"Erstellen Sie hier ein Ticket, indem Sie den 📩-Button drücken. Damit können Moderatoren privat kontaktiert werden, um Server Angelegenheiten zu klären."

            view = discord.ui.View(timeout=None)
            view.add_item(CreateTicketButton(self.guild, self.ticketCategory, self.logChannel, self.maxClosedTickets, self.permissions))

            oldMessageId : discord.Message = self.cfg.c().get(DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_OLD_TICKET_MESSAGEID)

            #edit old message if it exists
            if oldMessageId != None:
                oldMessage = await self.ticketChannel.fetch_message(oldMessageId)
                await oldMessage.edit(embed=ticketChannelEmbed, view=view)

            #or send new message
            else:
                msg : discord.Message  = await self.ticketChannel.send(embed=ticketChannelEmbed, view=view)
                self.cfg.c().update({DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_OLD_TICKET_MESSAGEID:msg.id})
                self.cfg.save()

            self.setup_tickets_on_startup = True


    async def get_channels_on_ready(self):
        #get log and ticket channel

        self.logChannel = self.client.get_channel(self.logChannelId)
        
        if self.logChannel == None:
            logging.critical(f"{self.moduleName} could not load logChannel.")

        self.ticketChannel = self.client.get_channel(self.ticketChannelId)

        if self.ticketChannel == None:
            logging.critical(f"{self.moduleName} could not load ticketChannel.")


        self.guild  = self.client.get_guild(self.client.guildID.id)

        self.ticketCategory = discord.utils.get(self.guild.categories, id=self.ticketCategoryId)  

    def setup(self):
        # load the config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        # load log channel id
        self.logChannelId = self.channels.getLogChannelId()

        if self.logChannelId == None:
            logging.critical(f"{self.moduleName} could not load logChannelId.")

            return False

        #load ticket channel id
        self.ticketChannelId = self.channels.getTicketChannelId()

        if self.ticketChannelId == None:
            logging.critical(f"{self.moduleName} could not load ticketChannelId.")

            return False

        #load ticketCategoryId
        self.ticketCategoryId = self.categories.getTicketCategoryId()

        if self.ticketCategoryId == None:
            logging.critical(f"{self.moduleName} could not load ticketCategoryId")

            return False

        #load max closed-active ticket count
        self.maxClosedTickets= self.cfg.c().get(DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_MAX_CLOSED_ACTIVE_TICKETS)

        if self.maxClosedTickets == None:
            logging.critical(f"{self.moduleName} could not load Max closed-active tickets")

            return False

        # initialize the permission config
        try:
            self.permissions = FlugPermissions.FlugPermissions(
                self.cfg.c().get(DEFAULT_FLUGVOGEL_TICKETS_CFG_PERMISSIONS),
                self.roles, self.users
            )
        except Exception as e:
            logging.critical(f"Failed to setup permission config for {self.moduleName}!")
            logging.exception(e)

            return False

        # register the event handler to get the log and ticket channels
        self.client.addSubscriber("on_ready", self.get_channels_on_ready)
        self.client.addSubscriber("on_ready", self.setup_tickets_on_startup)
      

        return True

CLASS = FlugTickets
