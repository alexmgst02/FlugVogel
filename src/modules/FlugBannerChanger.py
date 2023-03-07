import logging
import asyncio
from astral import LocationInfo, sun
from astral.sun import sun

import datetime

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

import util.logHelper
import util.flugPermissionsHelper

DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_PERMISSIONS = "permissions"
DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_MANAGE = "configure_banner"
DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_DYNAMIC_TIME_KEY = "dynamicSunBasedTimes"
DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_PATH_DAYBANNER = "pathToDayBanner"
DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_PATH_NIGHTBANNER = "pathToNightBanner"

class FlugBannerChanger(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig
    permissions: FlugPermissions.FlugPermissions = None
    guild: discord.Guild
    startupDone: bool = False
    logChannelId: int = None
    logChannel: discord.TextChannel = None
    dayBannerPath: str
    nightBannerPath: str
    dynamicTimeChanges: bool = False 
    nextSunset: datetime.datetime
    nextSunrise: datetime.datetime
    nextChangeTime: datetime.datetime

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

    async def get_log_channel_on_ready(self):
        if self.startupDone:
            return
        
        self.guild = self.client.getGuild()

        self.logChannel = self.client.get_channel(self.logChannelId)

        if self.logChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the log channel ({self.logChannelId})!")


        self.startupDone = True
        if not self.changeBannerDynamic.is_running():
            self.changeBannerDynamic.start()

    def setup(self):
        # load the config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        self.logChannelId = self.channels.getLogChannelId()

        if self.logChannelId == None:
            logging.critical(f"{self.moduleName} could not load log channel")
            
            return False

        self.dayBannerPath = self.cfg.c().get(DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_PATH_DAYBANNER)

        if self.dayBannerPath == None:
            logging.critical(f"{self.moduleName} could not load path to banner.")
            
            return False
        
        self.nightBannerPath = self.cfg.c().get(DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_PATH_NIGHTBANNER)

        if self.nightBannerPath == None:
            logging.critical(f"{self.moduleName} could not load path to banner.")
            
            return False

        # initialize the permission config
        try:
            self.permissions = FlugPermissions.FlugPermissions(
                self.cfg.c().get(DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_PERMISSIONS),
                self.roles, self.users
            )
        except Exception as e:
            logging.critical(f"Failed to setup permission config for {self.moduleName}!")
            logging.exception(e)

        # register the event handler to get the log channel
        self.client.addSubscriber('on_ready', self.get_log_channel_on_ready)

        @self.client.tree.command(description="Stop or restart automatic banner changes")
        async def managebannerchanger(interaction: discord.Interaction):
            if not await util.flugPermissionsHelper.canDoWrapper(DEFAULT_FLUGVOGEL_BANNER_CHANGER_CFG_MANAGE, interaction.user, 
                None, self.permissions, self.logChannel):
                await interaction.response.send_message(f"Sie dürfen den BannerChanger nicht konfigurieren! Dieser Vorfall wird gemeldet 🚔!", ephemeral=True)
                return
            
            if self.changeBannerDynamic.is_running():
                self.changeBannerDynamic.cancel()
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, f"{self.moduleName}", f"Automatic banner change has been disabled by {interaction.user.mention}")
                await interaction.response.send_message("Automatic banner change has been disabled", ephemeral=True)
                return

            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, f"{self.moduleName}", f"Automatic banner change has been enabled by {interaction.user.mention}")
            self.changeBannerDynamic.start()
            await interaction.response.send_message("Automatic banner change has been enabled", ephemeral=True)

        return True
    @tasks.loop(hours=24)
    async def changeBannerDynamic(self):
        pathToPic = ""
        present = datetime.datetime.now(datetime.timezone.utc)
        tmrw = present + datetime.timedelta(days=1)
        berlin = LocationInfo("Berlin")
        s = sun(berlin.observer, date=datetime.date.today())
        st = sun(berlin.observer, date=tmrw)
        sunrise = s["sunrise"]
        sunset = s["sunset"]

        sunriseDiff = (sunrise - present).total_seconds()
        sunsetDiff = (sunset - present).total_seconds()
        
        if sunriseDiff > 0:
            waitTimeOne = sunriseDiff
            waitTimeTwo = (sunset - sunrise).total_seconds()
            pathToPicOne = self.dayBannerPath
            pathToPicTwo = self.nightBannerPath

        elif sunsetDiff > 0:
            waitTimeOne = sunsetDiff
            waitTimeTwo = (st["sunrise"] - sunset).total_seconds()
            pathToPicOne = self.nightBannerPath
            pathToPicTwo = self.dayBannerPath

        else:
            await asyncio.sleep(60*60*9)
            self.changeBannerDynamic.restart()
            return


        timesWithPath = {waitTimeOne:pathToPicOne,
                          waitTimeTwo:pathToPicTwo}

        for waitTime, path in timesWithPath.items():

            await asyncio.sleep(waitTime)

            with open(path, "rb") as f:
                await self.guild.edit(banner=f.read())

                time = "day"
                if path == self.nightBannerPath:
                    time = "night"

                await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, self.moduleName, f"Set {time} banner.")
        

CLASS = FlugBannerChanger
