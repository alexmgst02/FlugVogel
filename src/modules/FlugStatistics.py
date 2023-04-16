import datetime
import logging
import typing
import random
import re

import discord
from discord.ext import tasks

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugCategories
import FlugRoles
import FlugUsers
import FlugConfig
import FlugPermissions

import util.flugPermissionsHelper
import util.logHelper

DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_PRIOR_COUNT = "priorMemberCount"
DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_PERMISSIONS = "permissions"
DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_STATS_WINDOW_H = "generalStatisticsWindowHours"
DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_ONELINERS = "generalStatisticsOneliners"
DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_DEFAULT_CHANNEL_IGNORE = "generalStatisticsChannelDefaultIgnore"
DEFAULT_FLUGVOGEL_STATISTICS_CFG_PERMISSIONS_GENERATE_STATS = "generateGeneralStatistics"
DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_LAST_TIME = "lastTimestampStatistics"
DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_TIMEFRAME = "statisticsTimeframeMinutes"

class FlugStatistics(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig
    logChannelId: int
    logChannel: discord.TextChannel
    statChannelId: int
    statChannel: discord.TextChannel
    guild: discord.Guild
    memberCountChannelId: int = None
    memberCountChannel: discord.VoiceChannel = None    
    priorMemberCount: int  = None
    permissions : FlugPermissions.FlugPermissions = None
    statsWindowH : int = None
    channelDefaultIgnore : bool = None
    oneliners : typing.List[str] = None
    lastGeneralStatisticsTime: datetime.datetime = None
    timeframe: int = None

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

    async def get_guild_and_channels_on_ready(self):
        self.guild = self.client.getGuild()

        self.logChannel = self.client.get_channel(self.logChannelId)
        self.memberCountChannel = self.client.get_channel(self.memberCountChannelId)
        self.statChannel = self.client.get_channel(self.statChannelId)

        # start backlground loop
        if not self.statistics_member_count.is_running():
            self.statistics_member_count.start()

        if not self.general_statistics_background_loop.is_running():
            self.general_statistics_background_loop.start()

    def setup(self):
        # load the config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")


        # get channel IDs and fail if one is missing
        self.memberCountChannelId = self.channels.getChannelId(FlugChannels.DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_MEMBER_COUNT)

        if self.memberCountChannelId == None:
            logging.critical(f"No ID found for the Member-Count-Channel: {self.moduleName}")

            return False

        self.logChannelId = self.channels.getChannelId(FlugChannels.DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_LOG)

        if self.logChannelId == None:
            logging.critical(f"No ID found for the Log-Channel: '{self.moduleName}'!")

            return False

        self.statChannelId = self.channels.getChannelId(FlugChannels.DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_STATISTICS)

        if self.statChannelId == None:
            logging.critical(f"No ID found for the Statistics-Channel: '{self.moduleName}'")

            return False

        # get the saved/prior member count
        self.priorMemberCount = self.cfg.c().get(DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_PRIOR_COUNT)

        if self.priorMemberCount == None:
            self.priorMemberCount = 0

        # get the statistics window
        self.statsWindowH = self.cfg.c().get(DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_STATS_WINDOW_H)

        if self.statsWindowH == None:
            logging.critical(f"No statistics time window found (key={DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_STATS_WINDOW_H}): '{self.moduleName}'")

            return False

        # get the channel-default-ignore value
        self.channelDefaultIgnore = self.cfg.c().get(DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_DEFAULT_CHANNEL_IGNORE)

        if self.channelDefaultIgnore == None:
            logging.critical(f"No channel-default-ignore value found (key={DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_DEFAULT_CHANNEL_IGNORE}): '{self.moduleName}'")

            return False

        # get the list of oneliners
        self.oneliners = self.cfg.c().get(DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_ONELINERS)

        if self.oneliners == None:
            logging.critical(f"No oneliners found (key={DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_ONELINERS}): '{self.moduleName}'")

            return False

        self.timeframe = self.cfg.c().get(DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_TIMEFRAME)

        if self.timeframe == None:
            logging.critical(f"No oneliners found (key={DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_TIMEFRAME}): '{self.moduleName}'")

            return False
        
        self.lastGeneralStatisticsTime = self.cfg.c().get(DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_LAST_TIME)

        if self.lastGeneralStatisticsTime != None:
            self.lastGeneralStatisticsTime = datetime.datetime.strptime(self.lastGeneralStatisticsTime, "%Y-%m-%d %H:%M:%S.%f")

        # register the event handler to get the log channel
        self.client.addSubscriber('on_ready', self.get_guild_and_channels_on_ready)

        # initialize the permission config
        try:
            self.permissions = FlugPermissions.FlugPermissions(
                self.cfg.c().get(DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_PERMISSIONS),
                self.roles, self.users
            )
        except Exception as e:
            logging.critical(f"Failed to setup permission config for {self.moduleName}!")
            logging.exception(e)

            return False

        ###### Regular statistics ######
        @self.client.tree.command(description="Statistiken für einen konfigurierten Zeitraum.")
        async def general_statistics(interaction: discord.Interaction):
            # buy us some time
            await interaction.response.defer(ephemeral=True, thinking=True)

            # check whether the calling user is allowed to use this command
            allowed = await util.flugPermissionsHelper.canDoWrapper(
                DEFAULT_FLUGVOGEL_STATISTICS_CFG_PERMISSIONS_GENERATE_STATS,
                interaction.user, None, self.permissions, self.logChannel
            )
        
            if not allowed:
                await interaction.followup.send("Die Nutzung dieses Befehls ist für Sie untersagt! Dieser Vorfall wird gemeldet 🚔!", ephemeral=True)

                return

            # actually generate the statistics
            await self.generate_general_statistics()

            await interaction.followup.send(f"Die Statistiken wurden soeben nach {self.statChannel.mention} entsandt!", ephemeral=True)  

            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, self.moduleName, f"{interaction.user.mention} requested general statistics. They have been sent to {self.statChannel.mention}")          
    
        @self.client.tree.command(description="set parameters for statstics loop")
        @discord.app_commands.describe(
            timeframe="Time between stats updates in minutes",
            restart_loop="restart the loop now"
        )
        async def manage_statistics(interaction: discord.Interaction, timeframe: typing.Optional[int], restart_loop: typing.Optional[bool]):
            if not await util.flugPermissionsHelper.canDoWrapper(DEFAULT_FLUGVOGEL_STATISTICS_CFG_PERMISSIONS_GENERATE_STATS, interaction.user, None, self.permissions, self.logChannel):
                await interaction.response.send_message("Die Nutzung dieses Befehls ist für Sie untersagt! Dieser Vorfall wird gemeldet 🚔!", ephemeral=True)
                return
            
            logText = ""

            if timeframe:
                self.timeframe = timeframe
                self.cfg.c().update({DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_TIMEFRAME:timeframe})
                self.cfg.save()
                logText += f"set general_statistics timeframe to {timeframe}"

            #next time background check is done, it will generate stats
            if restart_loop:
                self.lastGeneralStatisticsTime = None
                if logText != "":
                    logText += "and "
                logText += "restarted loop. The next background check will generate statistics."

            await interaction.response.send_message(f"Succesfully updated stats settings. See {self.logChannel.mention} for more detail.", ephemeral=True)
            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, self.moduleName, f"{interaction.user.mention} {logText}")

        return True        

    async def generate_general_statistics(self):
        # (name, id)
        unknownChannels = []

        # get the current time and the beginning of the stats window
        now = datetime.datetime.now()
        begin = now - datetime.timedelta(hours=self.statsWindowH)

        # counters
        messageCntr = channelCntr = 0
        channelCntrs = {}  # each channel (by id) will get a message coutner
        emoteCntrs = {}    # count emote occurances
        userMsgCntrs = {}  # count messages per user
        reactionCntrs = {} # count reaction emote occurances

        logging.info("Starting to read messages for statistics ...")

        ### message scanning/"stuff" counting ###
        # iterate over and filter channels
        channel : discord.channel.TextChannel
        for channel in self.guild.text_channels:
            # keep track of the messages for this channel
            channelMsgCntr = 0

            # get the config for this channel to check whether it should be ignored
            channelCfg = self.channels.getChannelConfig(str(channel.id))

            # ignore the channel if we don't know it and if default set, but leave a warning
            if channelCfg == None:
                # can't be pulled into condition above, as elif is not allowed to run when channelCfg == None
                if self.channelDefaultIgnore == True:
                    unknownChannels.append((channel.name, channel.id))

                    continue
            elif channelCfg.get(FlugChannels.DEFAULT_FLUGVOGEL_CFG_KEY_CHANNEL_STATS_IGNORE, None) == True:
                # check whether it should be ignored
                continue

            # we have a valid channel
            channelCntr += 1

            # scan for messages in this channel
            async for msg in channel.history(limit=None, after=begin):
                # increase message counters
                channelMsgCntr += 1
                messageCntr += 1

                userMsgCntrs.update({msg.author.id: userMsgCntrs.get(msg.author.id, 0) + 1})

                # scan for emotes
                emoteStr : str
                for emoteStr in re.findall(r'<:\w*:\d*>', msg.content):
                    # emotes have the format described in the regex above; \d part is the id - extract it
                    try:
                        emoteId = int(emoteStr.split(":")[2].removesuffix(">"))
                    except IndexError as e:
                        logging.warning("Caught broken emote '{emote}' when scanning messages for statistics!")
                        continue

                    # try to get the emote/returns None for emotes from other servers
                    emote = self.client.get_emoji(emoteId)

                    if emote == None:
                        # ignore it
                        continue

                    # update the counter
                    emoteCntrs.update({emote: emoteCntrs.get(emote, 0) + 1})

                # count reactions
                reaction : discord.Reaction
                for reaction in msg.reactions:
                    # non-custom emotes might be strings; then this will fails
                    try:
                        # get the emote manually to make sure its known to the server
                        emote = self.client.get_emoji(reaction.emoji.id)
                    except AttributeError as e:
                        continue

                    if emote == None:
                        # ignore it
                        continue

                    reactionCntrs.update({emote: reactionCntrs.get(emote, 0) + 1})
                    
            # set the channel counter
            channelCntrs.update({channel.id: channelMsgCntr})

        logging.info(f"Read {messageCntr} messages from {len(channelCntrs.keys())} channels ...")

        # log unknown channels
        if len(unknownChannels) > 0:
            await util.logHelper.logToChannelAndLog(
                self.logChannel, logging.WARNING, "FlugStatistics",
                f"Found {len(unknownChannels)} unknown channels ignored while scanning for general statistics (name, id): ```{unknownChannels}```"
            )

        ### build the output ###
        # get top emotes, users, ... - reverse makes it descending order
        topEmotes = sorted(emoteCntrs.items(), key=lambda x:x[1], reverse=True)
        topUsers = sorted(userMsgCntrs.items(), key=lambda x:x[1], reverse=True)
        topChannels = sorted(channelCntrs.items(), key=lambda x:x[1], reverse=True)
        topReactions = sorted(reactionCntrs.items(), key=lambda x:x[1], reverse=True)

        logging.info("Sorted all counters ...")

        # build the channel ranking string
        channelRankingStr = ""

        for i in range(min(3, len(channelCntrs.keys()))):
            channel = self.client.get_channel(topChannels[i][0])
            channelRankingStr += f"Platz {i+1}: {channel.mention} mit {topChannels[i][1]} Nachrichten\n"

        # build the emote ranking string
        emoteRankingStr = ""

        for i in range(min(3, len(emoteCntrs.keys()))):
            emoteRankingStr += f"Platz {i+1}: {topEmotes[i][0]} mit {topEmotes[i][1]} Verwendungen\n"

        # build the reaction ranking string
        reactionRankingStr = ""

        for i in range(min(3, len(reactionCntrs.keys()))):
            reactionRankingStr += f"Platz {i+1}: {topReactions[i][0]} mit {topReactions[i][1]} Verwendungen\n"

        # build the embed
        embed = discord.Embed(title="FlugStatistiken", color=discord.Colour.og_blurple())
        embed.add_field(name="Kanäle", value=channelRankingStr, inline=False)
        embed.add_field(name="Emotes", value=emoteRankingStr, inline=False)
        embed.add_field(name="Reaktionen", value=reactionRankingStr, inline=False)
        embed.set_footer(text=self.oneliners[random.randrange(0, len(self.oneliners))])

        # set the timestamp
        embed.timestamp = now

        logging.info("Built statistics-embed ...")

        ### send it ###
        await self.statChannel.send(embed=embed)

        logging.info(f"Sent statistics to the channel ({self.statChannelId}) ...")


    

    @tasks.loop(minutes=10)
    async def general_statistics_background_loop(self):
        now = datetime.datetime.now()

        if self.lastGeneralStatisticsTime == None:
            self.lastGeneralStatisticsTime = now
            self.cfg.c().update({DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_LAST_TIME:str(now)})
            self.cfg.save()
            await self.generate_general_statistics()
            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, self.moduleName, f"Automatically generated statistics. Next Update in {self.timeframe} minutes")
            return
            
        timeDiff = (now - self.lastGeneralStatisticsTime).total_seconds()/60

        if timeDiff < self.timeframe:
            return
        
        self.lastGeneralStatisticsTime = now
        self.cfg.c().update({DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_LAST_TIME:str(now)})
        self.cfg.save()
        await self.generate_general_statistics()
        await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, self.moduleName, f"Automatically generated statistics. Next Update in {self.timeframe} minutes")

        return
        
    ###### Member Count Updater ######
    @tasks.loop(minutes=3)
    async def statistics_member_count(self):
        members = self.guild.member_count

        if members != self.priorMemberCount:
            #update the counter
            await self.memberCountChannel.edit(name=f"Total Members: {members}")

            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "FlugStatistics", f"Updated member count from {self.priorMemberCount} to {members}.")

            #save new member counter
            self.priorMemberCount = members
            self.cfg._cfgObj.update({DEFAULT_FLUGVOGEL_STATISTICS_CFG_KEY_PRIOR_COUNT:self.priorMemberCount})
            self.cfg.save()

CLASS = FlugStatistics
