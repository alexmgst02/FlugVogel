#
# This file implements config handling.
#
import logging
import json

class FlugConfig:
    ##### Class Initialization Parameters ####
    cfgPath: str = None  # Path to the config file

    ##### Class Internal Variables #####
    _cfgStr: str = None  # The raw config string
    _cfgObj: dict = None # The config loaded as dictionary

    def __init__(self, cfgPath: str):
        """Initialize an instance of the FlugConfig class.

        `cfgPath` Path to the config file (`str`).
        """
        self.cfgPath = cfgPath

    def load(self) -> bool:
        """Read the config from the file set on Class-Initialization.
        
        Returns `True` on success, `False` on failure.
        """
        # read the config file
        try:
            with open(self.cfgPath, "r") as fd:
                self._cfgStr = fd.read()
                self._cfgObj = json.load(fd)
        except Exception as e:
            logging.critical("Failed to load config from '%s'!" % self.cfgPath)
            logging.exception(e)
            return False

        return True

    def getCfgObj(self) -> dict:
        """Return the config object
        
        Returns `None` if no config is loaded or a dictionary on success. (`dict`)
        """
        return self._cfgObj
