import logging

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugCategories
import FlugRoles
import FlugUsers
import FlugConfig


DEFAULT_FLUGVOGEL_STATUS_CFG_KEY_STATUS = "status"

class FlugStatus(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig
    status : str = None
    startupDone : bool = False

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

    async def set_status_on_ready(self):
        #don't want to spam the api
        if not self.startupDone:
            activity = discord.Game(name=self.status)
            await self.client.change_presence(activity=activity)
            logging.info(f"Set status to '{activity.name}'")
            
            self.startupDone = True

    def setup(self):
        # load the config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")

        self.status = self.cfg.c().get(DEFAULT_FLUGVOGEL_STATUS_CFG_KEY_STATUS)

        if self.status == None:
            logging.critical(f"{self.moduleName} could not load status from config")
            
            return False


        # register the event handler to get the log channel
        self.client.addSubscriber('on_ready', self.set_status_on_ready)

      

        return True

CLASS = FlugStatus
