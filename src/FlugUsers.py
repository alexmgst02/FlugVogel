#
# User Information Handling
#
import FlugConfig
import logging

DEFAULT_FLUGVOGEL_CFG_KEY_USERS_DEACTIVATED = "banned"
DEFAULT_FLUGVOGEL_CFG_KEY_USERS_NAME = "name"

class FlugUsers:
    _userConfigPath: dict = None             # store the user config path
    userConfig: FlugConfig.FlugConfig = None # store the actual user config (FlugConfig instance)

    def __init__(self, userConfigPath: str):
        self._userConfigPath = userConfigPath

        return

    def loadCfg(self) -> bool:
        # load the config file
        self.userConfig = FlugConfig.FlugConfig(self._userConfigPath, backup=True)

        if self.userConfig.load() != True:
            logging.critical("Failed to load User-Config from '%s'!" % self._userConfigPath)

            return False

        logging.info("User-Config loaded! It has %d entries!" % len(self.userConfig.c().keys()))

        return True

    def save(self) -> bool:
        # save the config file
        if self.userConfig.save() != True:
            logging.critical("Failed to save User-Config to '%s'!" % self._userConfigPath)

            return False

        return True

    def isConfigLoaded(self) -> bool:
        return self.userConfig != None

    def isUserKnown(self, id: str) -> bool:
        return self.userConfig.c().get(id, None) != None

    def getUserConfig(self, id: str) -> dict:
        return self.userConfig.c().get(id, None)

    def getUserID(self, name: str) -> int:
        # go through all user configs
        for key, config in self.userConfig.c().items():
            if config.get(DEFAULT_FLUGVOGEL_CFG_KEY_USERS_NAME, None) == name:
                return int(key)

        return None

    def isUserDeactivated(self, id: str) -> bool:
        if self.isUserKnown(id) and self.getUserConfig(id).get(DEFAULT_FLUGVOGEL_CFG_KEY_USERS_DEACTIVATED, False) == True:
            return True
        return False


