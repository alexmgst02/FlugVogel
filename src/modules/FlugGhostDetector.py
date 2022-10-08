import logging
import datetime
import json

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig
import FlugPermissions

# config keys
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD = "threshold"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS = "onlyPings"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_PERMISSIONS = "permissions"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_GHOST_PING_LOG_SIZE = "ghostPingLogSize"

DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_PERMISSIONS_ZEIGE_GEISTER_PINGS_OTHER_USER = "zeige_geister_pings_other_user"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_PERMISSIONS_SET_GHOST_DETECTOR_CONFIG = "set_ghost_detector_config"
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_PERMISSIONS_GET_GHOST_DETECTOR_CONFIG = "get_ghost_detector_config"

# config defaults
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_TRESHOLD = 30
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_ONLYPINGS = False
DEFAULT_FLUGVOGEL_GHOSTDETECTOR_GHOST_PING_LOG_SIZE = 20

# ghost ping log keys
DEFAULT_FLUGVOGEL_GHOSTPING_LOG_MENTION = "mention"
DEFAULT_FLUGVOGEL_GHOSTPING_LOG_ID = "id"
DEFAULT_FLUGVOGEL_GHOSTPING_LOG_TS = "ts"

class FlugGhostDetector(modules.FlugModule.FlugModule):
    logChannel: discord.abc.GuildChannel
    logChannelId: int = None
    onlyPings: bool = None
    treshold: int = None
    ghostPingLogSize: int = None
    permissions: FlugPermissions.FlugPermissions = None


    #
    # GhostPingLog which stores ghost pings so that users can check for it later; format:
    # {
    #   "<PINGED_USER_ID>": [
    #       ("<PINGING_USER_NAME1>", "<PINGING_USER_ID1>"),
    #       ...
    #   ],
    #   ...
    # }
    #
    ghostPingLog: dict = {}

    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))

    async def get_log_channel_on_ready(self):
        self.logChannel = self.client.get_channel(self.logChannelId)

        if self.logChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the log channel ({self.logChannelId})!")

    async def detect_ghost_on_message_delete(self, message : discord.Message):
        # get the relevant config values
        self.threshold = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD, DEFAULT_FLUGVOGEL_GHOSTDETECTOR_TRESHOLD)
        self.onlyPings = self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS, DEFAULT_FLUGVOGEL_GHOSTDETECTOR_ONLYPINGS)

        # check whether the time of deletion is below the threshold
        createdAt = message.created_at
        deletedAt = datetime.datetime.now(datetime.timezone.utc)
        difference = (deletedAt - createdAt).total_seconds()

        if difference > self.threshold and self.threshold != 0:
            return

        # determine whether the message is a reference and whether it's a ping (mention)
        reference = message.reference != None
        ping = len(message.mentions) > 0 or len(message.role_mentions) > 0 or message.mention_everyone
        
        # build the embed which reports the detected ghost reference/ping/message
        embed = discord.Embed(title="👻 Ghost Detector 👻")
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.timestamp = deletedAt

        # references are always mentions/pings; catch both here
        if ping or reference:
            embed.description = f"Possible Ghost-Ping"
            
            if reference:
                embed.description += "/Reference"

            # store the ghostping for all mentioned users
            for mention in message.mentions:
                if self.ghostPingLog.get(str(mention.id), None) == None:
                    self.ghostPingLog.update({str(mention.id): []})

                # add the message to the log
                self.ghostPingLog.get(str(mention.id)).append({
                    DEFAULT_FLUGVOGEL_GHOSTPING_LOG_MENTION: message.author.mention,
                    DEFAULT_FLUGVOGEL_GHOSTPING_LOG_ID: message.author.id,
                    DEFAULT_FLUGVOGEL_GHOSTPING_LOG_TS: f"{message.created_at}"
                })

                # check whether the maximum log size is exceeded
                if len(self.ghostPingLog.get(str(mention.id))) > self.ghostPingLogSize > 0:
                    self.ghostPingLog.get(str(mention.id)).pop(0)

                #DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_GHOST_PING_LOG_SIZE
        elif not self.onlyPings:
            embed.description = f"Ghost-Message"
        else:
            return

        embed.description += f"\nAuthor: {message.author.mention}\nDeleted after {difference} seconds\nOriginal Message: "

        if len(embed.description) + len(message.content) >= 2000:
            embed.description += "-- Original Message Too Long --"
        else:
            embed.description += message.content

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
                self.cfg.c().get(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_PERMISSIONS),
                self.roles, self.users
            )
        except Exception as e:
            logging.critical(f"Failed to setup permission config for {self.moduleName}!")
            logging.exception(e)

            return False

        # the the maximum log size
        self.ghostPingLogSize = self.cfg.c().get(
            DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_GHOST_PING_LOG_SIZE,
            DEFAULT_FLUGVOGEL_GHOSTDETECTOR_GHOST_PING_LOG_SIZE
        )

        if self.ghostPingLogSize == None:
            logging.critical(f"")

        # fail if no log channel is configured
        self.logChannelId = self.channels.getLogChannelId()

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel '{self.moduleName}'!")

            return False
        
        # register the event handlers
        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)
        self.client.addSubscriber('on_message_delete', self.detect_ghost_on_message_delete)

        @self.client.tree.command(description="Configure the FlugGhostDetector")
        @discord.app_commands.describe(
            treshold="Deletion of messages older than the threshold in seconds will be ignored (0 = Infinite).",
            only_pings="Only Register Pings and References.",
            ghostping_log_size="Amount of ghostpings to log per user."
        )
        async def set_ghost_detector_config(interaction: discord.Interaction, treshold: int, only_pings: bool, ghostping_log_size: int):
            # check the permissions
            perms = self.permissions.canDo(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_PERMISSIONS_SET_GHOST_DETECTOR_CONFIG, discord.user, None)

            if perms < FlugPermissions.FlugPermissions.CAN_DO_WEAK_NO:
                await interaction.response.send_message("Sie dürfen diesen Befehl nicht benutzen! Dieser Vorfall wird gemeldet 🚔!", ephemeral=True)

                return

            # save the changes
            self.cfg._cfgObj.update({
                DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_THRESHOLD:treshold,
                DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_ONLY_PINGS:only_pings,
                DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_GHOST_PING_LOG_SIZE:ghostping_log_size
            })

            self.cfg.save()

            # build an embed
            embed = discord.Embed(title="🚧 New Ghost Detector Config 🚧")
            embed.description = f"New 'treshold': {treshold}\nNew 'only_pings': {only_pings}\nNew 'ghostping_log_size': {ghostping_log_size}"

            # respond to the user-only and send to the log channel
            await interaction.response.send_message(
                f"Set new 'treshold': {treshold} and new 'only_pings': {only_pings}\nNew 'ghostping_log_size': {ghostping_log_size}", ephemeral=True
            )

            await self.logChannel.send(embed=embed)

        @self.client.tree.command(description="Get the FlugGhostDetector Configuration")
        async def get_ghost_detector_config(interaction: discord.Interaction):
            # check the permissions
            perms = self.permissions.canDo(DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_PERMISSIONS_GET_GHOST_DETECTOR_CONFIG, interaction.user, None)

            if perms < FlugPermissions.FlugPermissions.CAN_DO_WEAK_NO:
                await interaction.response.send_message("Sie dürfen diesen Befehl nicht benutzen! Dieser Vorfall wird gemeldet 🚔!", ephemeral=True)

                return

            # build an embed
            embed = discord.Embed(title="🚧 Current Ghost Detector Config 🚧")
            embed.description = json.dumps(self.cfg.c(), indent=4)

            await interaction.response.send_message(f"Config sent to {self.logChannel.mention}", ephemeral=True)
            await self.logChannel.send(embed=embed)

        @self.client.tree.command(description="Erhalte eine Liste von Leuten die dich gegeisterpinged haben.")
        @discord.app_commands.describe(
            subjekt="Nutzer für welchen die Ghostpings ermittelt werden sollen."
        )
        async def zeige_geister_pings(interaction: discord.Interaction, subjekt: discord.Member = None):
            interaction.response.defer()

            # if the user wants to get ghostpings for another user, check the perms
            if subjekt != None and subjekt.id != interaction.user.id:
                perms = self.permissions.canDo(
                    DEFAULT_FLUGVOGEL_GHOSTDETECTOR_CFG_PERMISSIONS_ZEIGE_GEISTER_PINGS_OTHER_USER, 
                    interaction.user, subjekt
                )

                # if the perms don't resolve, abort
                if perms <= FlugPermissions.FlugPermissions.CAN_DO_WEAK_NO:
                    logging.info(
                        f"User {interaction.user.name} ({interaction.user.id}) tried to see" +
                        f"Ghostpings for user {subjekt.name} ({subjekt.id}) - {FlugPermissions.FlugPermissions.CAN_DO_STRINGS[perms]}"
                    )

                    await interaction.response.send_message(
                        f"Ihnen fehlen die nötigen Befugnisse um die Geisterpings für {subjekt.mention} einzusehen! Dieser Vorfall wird gemeldet 🚔.", ephemeral=True
                    )

                    return

                # set the target to the subjekt
                target = subjekt
            else:
                # the calling user is the target
                target = interaction.user

            # get the pings
            pings = self.ghostPingLog.get(str(target.id), []) 

            # create an embed and list the mentions
            embed = discord.Embed(title="👻 Geister Pings 👻")
            
            if len(pings) == 1:
                embed.description = "Es liegt ein Geisterping gegen sie vor! Folgend die verantwortliche Person:\n"
            else:
                embed.description = f"Es liegen {len(pings)} Geisterpings gegen Sie vor!"

                if len(pings) != 0:
                    embed.description += " Folgend die verantwortlichen Personen:\n"
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)

                    return
            
            # list all the pings
            for ping in pings:
                embed.description +=\
                    f"{ping.get(DEFAULT_FLUGVOGEL_GHOSTPING_LOG_MENTION)}\
                     ({ping.get(DEFAULT_FLUGVOGEL_GHOSTPING_LOG_ID)}) at\
                      {ping.get(DEFAULT_FLUGVOGEL_GHOSTPING_LOG_TS)}\n"

            await interaction.response.send_message(embed=embed, ephemeral=True)

        @self.client.tree.command(description="Entleere Ihr persönliches Geisterpingpostfach.")
        async def entleere_geister_pings(interaction: discord.Interaction):
            interaction.response.defer()

            # get the pings
            pings = self.ghostPingLog.get(str(interaction.user.id), []) 

            l = len(pings)

            if l == 0:
                await interaction.response.send_message("Ihr Geisterpingpostfach ist bereits entleert 📯!", ephemeral=True)
            else:
                self.ghostPingLog.update({
                    str(interaction.user.id): []
                })

                await interaction.response.send_message(f"Es wurden {l} Elemente aus ihrem Geisterpingpostfach entfernt 📯!", ephemeral=True)

            return

        return True


CLASS = FlugGhostDetector
