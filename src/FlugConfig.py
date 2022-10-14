#
# This file implements config handling.
#
import logging
import json
import shutil

class FlugConfig:
    ##### Class Initialization Parameters ####
    cfgPath: str = None  # Path to the config file
    backup: bool = True  # Controls on-save-backups

    ##### Class Internal Variables #####
    _cfgObj: dict = None # The config loaded as dictionary

    def __init__(self, cfgPath: str, backup: bool = True):
        """Initialize an instance of the FlugConfig class.

        `cfgPath` Path to the config file (`str`).

        `backup` If set to `True`, a backup will be made when saving a config.
        It will be called `{FILENAME}.backup` (`bool`).
        """
        self.cfgPath = cfgPath
        self.backup = backup

    def load(self) -> bool:
        """Read the config from the file set on Class-Initialization.
        
        Returns `True` on success, `False` on failure.
        """
        # read the config file
        try:
            with open(self.cfgPath, "r") as fd:
                self._cfgObj = json.load(fd)
        except Exception as e:
            logging.critical("Failed to load config from '%s'!" % self.cfgPath)
            logging.exception(e)
            
            return False

        return True

    def save(self) -> bool:
        """Write the loaded config to the file set on Class-Initialization.

        Returns `True` on success, `False` on failure.
        """
        # check whether the current config should be backuped
        if self.backup == True:
            shutil.copy2(self.cfgPath, self.cfgPath + ".backup")

        try:
            with open(self.cfgPath, "w") as fd:
                json.dump(self._cfgObj, fd, indent=4)
        except Exception as e:
            logging.critical("Failed to save config to '%s'!" % self.cfgPath)
            logging.exception(e)

            return False
        
        return True

    def c(self) -> dict:
        """Return the config object
        
        Returns `None` if no config is loaded or a dictionary on success. (`dict`)
        """
        return self._cfgObj
