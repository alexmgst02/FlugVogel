import logging
import asyncio

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig

import util.logHelper

DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_CATEGORYID = "ticketCategoryId"
DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_OLD_TICKET_MESSAGEID = "ticketMessageId"


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

    def __init__(self, guild : discord.Guild, ticketChannel : discord.TextChannel, logChannel : discord.TextChannel, ticketCreator : discord.Member):
        super().__init__(label="🔒Bestätigen🔒", style=discord.ButtonStyle.red)
        self.ticketChannel = ticketChannel
        self.guild = guild
        self.logChannel = logChannel
        self.ticketCreator = ticketCreator

    async def callback(self, interaction : discord.Interaction):
        await interaction.response.defer()

        if interaction.user.id == self.ticketCreator.id:
            await self.ticketChannel.set_permissions(self.ticketCreator, read_messages=False, send_messages=False)
            await interaction.followup.send(f"closed ticket for {interaction.user.mention}")

        else:
            await interaction.followup.send("closed ticket, deleting channel.")
            await asyncio.sleep(3)
            await self.ticketChannel.delete()



class TicketButton(discord.ui.Button):
    guild : discord.Guild = None
    logChannel : discord.TextChannel = None    
    ticketChannel : discord.TextChannel = None
    ticketCreator : discord.Member = None

    def __init__(self, guild : discord.Guild, ticketChannel : discord.TextChannel, logChannel : discord.TextChannel, ticketCreator : discord.Member):
        super().__init__(label="🔒Ticket schließen", style=discord.ButtonStyle.gray)
        self.ticketChannel = ticketChannel
        self.guild = guild
        self.logChannel = logChannel
        self.ticketCreator = ticketCreator

    async def callback(self, interaction : discord.Interaction):
        view = discord.ui.View()
        closeBtn = CancelTicketButton(self.guild, self.ticketChannel, self.logChannel, self.ticketCreator)
        cancelButton = CancelButton(self.guild, interaction)
        view.add_item(closeBtn)
        view.add_item(cancelButton)
        await interaction.response.send_message(f"Sicher, {interaction.user.mention}?", view=view)


class CreateTicketButton(discord.ui.Button):
    guild : discord.Guild = None
    logChannel : discord.TextChannel = None

    ticketCategory : discord.CategoryChannel = None
    def __init__(self, guild : discord.Guild, ticketCategory : discord.CategoryChannel, logChannel : discord.TextChannel):
        super().__init__(label="📩 Ticket erstellen", style=discord.ButtonStyle.gray)
        self.ticketCategory = ticketCategory
        self.guild = guild
        self.logChannel = logChannel

    async def callback(self, interaction: discord.Interaction):
        ticketChannelName = f"ticket-{interaction.user.id}" #must be unique
        await interaction.response.defer(ephemeral=True)

        #check if user already has an open ticket. otherwise create new ticket.
        existingChannel = discord.utils.get(self.guild.text_channels, name=ticketChannelName)
        if existingChannel != None:
            await interaction.followup.send(f"Es existiert bereits das Ticket {existingChannel.mention}", ephemeral=True)
            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "📩FlugTickets📩", f"{interaction.user.mention} tried to open second ticket.")

            return

        
        #create channel first - it syncs perms with the catgory
        newChannel = await self.ticketCategory.create_text_channel(ticketChannelName)
    
        #get member to set perms
        member = self.guild.get_member(interaction.user.id)

        #update perms
        await newChannel.set_permissions(member, read_messages=True, send_messages=True)

        await interaction.followup.send(f"Ticket erstellt: {newChannel.mention}", ephemeral=True)

        #setup ticket view and embed
        view = discord.ui.View()
        ticketButton = TicketButton(self.guild, newChannel, self.logChannel, member)
        view.add_item(ticketButton)

        await newChannel.send("HI", view=view)


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

    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users)


        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))


    async def setup_tickets_on_startup(self):
        if not self.startupDone:            

            ticketChannelEmbed = discord.Embed(color=discord.Color.green())
            ticketChannelEmbed.set_author(name=self.client.user.name, icon_url=self.client.user.display_avatar.url) 
            ticketChannelEmbed.title = "Moderatoren kontaktieren"
            ticketChannelEmbed.description = f"Erstellen Sie hier ein Ticket, indem Sie den 📩-Button drücken."

            view = discord.ui.View()
            view.add_item(CreateTicketButton(self.guild, self.ticketCategory, self.logChannel))

            oldMessageId : discord.Message = self.cfg.c().get(DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_OLD_TICKET_MESSAGEID)

            #edit old message
            if oldMessageId != None:
                oldMessage = await self.ticketChannel.fetch_message(oldMessageId)
                await oldMessage.edit(embed=ticketChannelEmbed, view=view)
            #send new message
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
        self.ticketCategoryId = self.cfg.c().get(DEFAULT_FLUGVOGEL_CFG_KEY_TICKETS_CATEGORYID)

        if self.ticketCategoryId == None:
            logging.critical(f"{self.moduleName} could not load ticketCategoryId")

            return False

        # register the event handler to get the log and ticket channels
        self.client.addSubscriber("on_ready", self.get_channels_on_ready)
        self.client.addSubscriber("on_ready", self.setup_tickets_on_startup)
      

        return True

CLASS = FlugTickets
