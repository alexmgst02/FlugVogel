#
# Channel Information Handling
#
import FlugConfig

import logging

DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_LOG = "log"
DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_REPORT = "report"
DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_NAME = "name"
DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_IS_ROLE_ASSIGNMENT = "isRoleAssignmentChannel"
DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_TICKETS = "ticketChannel"
DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_MEMBER_COUNT = "memberCountChannel"

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

    def getChannelName(self, id: str) -> str:
        cfg = self.getChannelConfig(id)

        if cfg == None:
            return None
        
        return cfg.get(DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_NAME)

    def getChannelId(self, key: str):
        channelID = self.getChannelConfig(key)

        if channelID == None:
            return None

        return int(channelID)        

    def getLogChannelId(self) -> int:
        #get the config for the log channel
        return self.getChannelId(DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_LOG)

    def getReportChannelId(self) -> int:
        #get the config for the report channel
        return self.getChannelId(DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_REPORT)

    def getTicketChannelId(self):
        #get the config for the ticket channel
        return self.getChannelId(DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_TICKETS)

    def getMemberCountChannelId(self):
        #get the config for the memberCount statistic channel
        return self.getChannelId(DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_MEMBER_COUNT)


    def isChannelRoleAssignment(self, id: str) -> bool:
        if self.isChannelKnown(id):
            if self.getChannelConfig(id).get(DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_IS_ROLE_ASSIGNMENT, False) == True:
                return True
        
        return False 

