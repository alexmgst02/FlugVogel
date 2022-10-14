#
# Handle Module Loading and initialization
#
import FlugChannels
import FlugClient
import FlugUsers
import FlugRoles
import FlugConfig

import modules.FlugModule

import importlib
import logging

# config file field names
DEFAULT_FLUGVOGEL_MODULES_CFG_NAME = "name"
DEFAULT_FLUGVOGEL_MODULES_CFG_CONFIG = "config"
DEFAULT_FLUGVOGEL_MODULES_CFG_OPTIONAL = "optional"
DEFAULT_FLUGVOGEL_MODULES_CFG_ENABLED = "enabled"

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
            # check whether the module has a name
            if moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_NAME, None) == None:
                logging.critical("Invalid module entry without a name in module config!")

                return False

            # check whether the module should be loaded
            if moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_ENABLED, False) == False:
                logging.info("Skipping disabled module '%s'" % moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_NAME))

                continue
            
            # import the module
            try:
                _module = importlib.import_module("modules." + moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_NAME))
                _module_cls : modules.FlugModule.FlugModule = _module.CLASS
            
            except Exception as e:
                logging.critical("Failed to import module '%s'!" % moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_NAME))
                logging.exception(e)

                return False
            
            # initilize the module
            try:
                module : modules.FlugModule.FlugModule = _module_cls(
                    moduleCfg.get("name"), moduleCfg.get("config"),
                    self.client, self.channels, self.roles, self.users
                )
            except Exception as e:
                logging.critical("Failed to initialize module '%s'!" % moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_NAME))
                logging.exception(e)

                if moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_OPTIONAL):
                    logging.info("Ignoring module load failure (optional = True)")
                else:
                    return False

            # run the module setup
            if module.setup() != True:
                logging.critical("Module setup for '%s' failed!" % moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_NAME))

                if moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_OPTIONAL):
                    logging.info("Ignoring module setup failure (optional = True)")
                else:
                    return False

            logging.info("Loaded and initialized module '%s'!" % moduleCfg.get(DEFAULT_FLUGVOGEL_MODULES_CFG_NAME))

        return True

    def isConfigLoaded(self) -> bool:
        return self.moduleConfig != None
