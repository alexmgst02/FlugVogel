#
# Handle Module Loading and initialization
#
from pydoc import cli
import FlugChannels
import FlugClient
import FlugUsers
import FlugRoles
#
# Thils file handles module loading & initialization
#

import FlugConfig

import importlib
import logging

class FlugModules:
    _moduleConfigPath: dict = None             # store the module config path
    moduleConfig: FlugConfig.FlugConfig = None # store the actual module config (FlugConfig instance)
    moduleList: list = []                      # a list to keep track of loaded modules
    client: FlugClient.FlugClient = None       # FlugClient instance for the modules
    channels: FlugChannels.FlugChannels = None # FlugChannel instance for the modules
    users: FlugUsers.FlugUsers = None          # FlugUsers instance for the modules
    roles: FlugRoles.FlugRoles = None          # FlugRoles instance for the modules

    def __init__(self, flugConfigPath: str,
            client: FlugClient.FlugClient,
            channelConfig: FlugChannels.FlugChannels,
            userConfig: FlugUsers.FlugUsers,
            roleConfig: FlugRoles.FlugRoles):
        self._moduleConfigPath = flugConfigPath
        self.client = client
        self.channels = channelConfig
        self.users = userConfig
        self.roles = roleConfig

        return

    def loadCfg(self) -> bool:
        # load the config file
        self.moduleConfig = FlugConfig.FlugConfig(self._moduleConfigPath)

        if self.moduleConfig.load() != True:
            logging.critical("Failed to load Module-Config from '%s'!" % self._moduleConfigPath)

            return False

        logging.info("Module-Config loaded! It has %d entries!" % len(self.moduleConfig.c()))

        return True

    def initModules(self) -> bool:
        # check if there are any modules
        if len(self.moduleConfig.c()) == 0:
            logging.warning("No modules to initialize!")

            return True

        # annotate moduleCfg (iterator)
        moduleCfg: dict

        # iterator through all module entries
        for moduleCfg in self.moduleConfig.c():
            module = None
            instance = None
            
            # import the module
            try:
                module = importlib.import_module("modules." + moduleCfg.get("name"))
            except Exception as e:
                logging.critical("Failed to import module '%s'!" % moduleCfg.get("name"))
                logging.exception(e)

                return False
            
            # initilize the module
            try:
                instance = module.init(
                    moduleCfg.get("name"), moduleCfg.get("config"),
                    self.client, self.channels, self.users, self.roles
                )
            except Exception as e:
                logging.critical("Failed to initialize module '%s'!" % moduleCfg.get("name"))
                logging.exception(e)

                return False

            self.moduleList.append({
                "cfg": moduleCfg.get("name"),
                "instance": instance
            })

            logging.info("Loaded and initialized module '%s'!" % moduleCfg.get("name"))

        return True

    def isConfigLoaded(self) -> bool:
        return self.moduleConfig != None
