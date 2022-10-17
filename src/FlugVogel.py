#
# FlugVogel Bot
#

import random
import sys
import logging
import FlugConfig
import FlugLoggerConfig
import FlugCredentials
import FlugChannels
import FlugCategories
import FlugUsers
import FlugRoles
import FlugModules
import FlugClient

# default locations for the config and token file
DEFAULT_FLUGVOGEL_CONFIG_PATH = "config.json"
DEFAULT_FLUGVOGEL_TOKEN_PATH = "token.json"

# default config keys for the main application
DEFAULT_FLUGVOGEL_CFG_KEY_GUILDID = "guildID"

DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG = "logConfig"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FORMAT = "logFormat"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_LEVEL = "logLevel"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE = "logFile"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE_SIZE = "logFileSize"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE_NUM = "logFileNum"

DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS = "channels"
DEFAULT_FLUGVOGEL_CFG_KEY_CATEGORIES = "categories"
DEFAULT_FLUGVOGEL_CFG_KEY_USERS = "users"
DEFAULT_FLUGVOGEL_CFG_KEY_ROLES = "roles"
DEFAULT_FLUGVOGEL_CFG_KEY_MODULES = "modules"

class FlugVogel:
    version: str = None                           # The Version of the FlugVogel
    simulate: bool = None                         # Simulate/log commands, but don't execute them
    cfgPath: str = None                           # Path to the config file
    tokenPath: str = None                         # Path to the token file
    cfg: FlugConfig.FlugConfig = None             # FlugConfig instance
    creds: FlugCredentials.FlugCredentials = None # FlugCredentials instance
    client: FlugClient.FlugClient = None          # FlugClient instance
    channels: FlugChannels.FlugChannels = None    # FlugChannels instance
    categories: FlugCategories.FlugCategories     # FlugCategories instance
    users: FlugUsers.FlugUsers = None             # FlugUsers instance
    roles: FlugRoles.FlugRoles = None             # FlugRoles instance
    modules: FlugModules.FlugModules = None       # FlugModules instance
    _initSuccess = False # Set to `True` once initialization succeeded

    def __init__(self, version: str, configPath: str = DEFAULT_FLUGVOGEL_CONFIG_PATH, tokenPath: str = DEFAULT_FLUGVOGEL_TOKEN_PATH):
        # set up the logger
        FlugLoggerConfig.FlugLoggerConfig.init()

        # set file paths
        self.cfgPath = configPath
        self.tokenPath = tokenPath

        # load the config
        self.cfg = FlugConfig.FlugConfig(self.cfgPath, backup=True)
        
        if not self.cfg.load():
            logging.critical("Failed to load FlugVogel-Config!")

            return

        if not self.cfg.save():
            logging.critical("Failed to save FlugVogel-Config!")

            return
        
        #set logger again with config
        logCfg = self.cfg.c()[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG]

        FlugLoggerConfig.FlugLoggerConfig.init(
            logFmt=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FORMAT],
            logLevel=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_LEVEL],
            logFile=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE],
            logFileSize=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE_SIZE],
            logFileNum=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE_NUM]
        )

        # load the credentials
        self.creds = FlugCredentials.FlugCredentials(self.tokenPath)

        if not self.creds.load():
            logging.critical("Failed to load FlugVogel-Credentials!")

            return

        # setup the channel config
        self.channels = FlugChannels.FlugChannels(self.cfg.c()[DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS])

        if not self.channels.loadCfg():
            logging.critical("Failed to load FlugVogel-Channels!")

            return

        # setup the category config
        self.categories = FlugCategories.FlugCategories(self.cfg.c()[DEFAULT_FLUGVOGEL_CFG_KEY_CATEGORIES])

        if not self.categories.loadCfg():
            logging.critical("Failed to load FlugVogel-Categories!")

            return


        # setup the user config
        self.users = FlugUsers.FlugUsers(self.cfg.c()[DEFAULT_FLUGVOGEL_CFG_KEY_USERS])

        if not self.users.loadCfg():
            logging.critical("Failed to load FlugVogel-Users!")

            return

        # setup the role config
        self.roles = FlugRoles.FlugRoles(self.cfg.c()[DEFAULT_FLUGVOGEL_CFG_KEY_ROLES])

        if not self.roles.loadCfg():
            logging.critical("Failed to load FlugVogel-Roles!")

            return

        # setup the client
        intents = FlugClient.discord.Intents.all()
        self.client = FlugClient.FlugClient(intents=intents,
            guildId=FlugClient.discord.Object(id=self.cfg.c().get(DEFAULT_FLUGVOGEL_CFG_KEY_GUILDID))
        )

        # load and initialize modules
        self.modules = FlugModules.FlugModules(
            self.cfg.c()[DEFAULT_FLUGVOGEL_CFG_KEY_MODULES],
            self.client, self.channels, self.users, self.roles, self.categories
        )

        if not self.modules.loadCfg():
            logging.critical("Failed to load FlugVogel-Roles!")

            return

        # initialize the modules
        if not self.modules.initModules():
            logging.critical("Failed to initialize modules!")

            return

        # made it here; success
        self._initSuccess = True

        return

    def initWasSuccess(self) -> bool:
        """Check whether initialization succeeded.

        Returns `True` if initialization was a success, `False` otherwise. (`bool`)
        """
        return self._initSuccess

    def flieg(self):
        # check whether initialization worked
        if not self.initWasSuccess():
            logging.critical("Initialization didn't succeed! I refuse to flieg!")

            return

        # start the client
        self.client.run(self.creds.getToken(), log_handler=None)

if __name__ == "__main__":
    # check for parameters
    if len(sys.argv) < 3:
        print("Usage: python3 %s <config_path> <token_path>" % (sys.argv[0]))

        sys.exit(-1)

    vogel = FlugVogel("0.0.1", configPath=sys.argv[1], tokenPath=sys.argv[2])

    vogel.flieg()
