#
# Channel Information Handling
#
import FlugConfig
import logging

class FlugChannels:
    _channelConfigPath: dict = None             # store the channel config path
    channelConfig: FlugConfig.FlugConfig = None # store the actual channel config (FlugConfig instance)

    def __init__(self, channelConfigPath: str):
        self._channelConfigPath = channelConfigPath

        return

    def loadCfg(self) -> bool:
        # load the config file
        self.channelConfig = FlugConfig.FlugConfig(self._channelConfigPath)

        if self.channelConfig.load() != True:
            logging.critical("Failed to load Channel-Config from '%s'!" % self._channelConfigPath)

            return False

        logging.info("Channel-Config loaded! It has %d entries!" % len(self.channelConfig.c().keys()))

        return True

    def save(self) -> bool:
        # save the config file
        if self.channelConfig.save() != True:
            logging.critical("Failed to save Channel-Config to '%s'!" % self._channelConfigPath)

            return False

        return True

    def isConfigLoaded(self) -> bool:
        return self.channelConfig != None

    def isChannelKnown(self, id: str) -> bool:
        return self.channelConfig.c().get(id, None) != None

    def getChannelConfig(self, id: str) -> dict:
        return self.channelConfig.c().get(id, None)
