#
# Channel Information Handling
#
import FlugConfig
import logging

class FlugChannels:
    _channelConfig: dict = None      # store the channel config (pre-stage)
    channelConfig: dict = None       # store the actual channel config

    def __init__(self, channelConfig: any):
        self._channelConfig = channelConfig

        return

    def load(self) -> bool:
        # check whether it's a config or a path
        if type(self._channelConfig) == dict:
            self.channelConfig = self._channelConfig
        elif type(self._channelConfig) == str:
            # load the config file
            cfg = FlugConfig.FlugConfig(self._channelConfig)

            if cfg.load() != True:
                logging.critical("Failed to load Channel Config from '%s'!" % self._channelConfig)

                return False

            # copy the config
            self.channelConfig = cfg.getCfgObj()
        else:
            logging.critical("'channelConfig' value of an unknown type (neither 'int' nor 'str'): %s" % str(self._channelConfig))

            return False

        logging.info("Channel config loaded! It has %d entries!" % len(self.channelConfig.keys()))

        return True

    def isConfigLoaded(self) -> bool:
        return self.channelConfig != None

    def doesChannelExist(self, id: str) -> bool:
        return self.channelConfig.get(id, None) != None

    def getChannelConfig(self, id: str) -> dict:
        return self.channelConfig.get(id, None)