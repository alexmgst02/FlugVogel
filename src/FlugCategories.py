#
# Category Information Handling
#
import FlugConfig

import logging

DEFAULT_FLUGVOGEL_CFG_KEY_CATEGORIES_TICKETS = "ticketCategory"
DEFAULT_FLUGVOGEL_CFG_KEY_CATEGORIES_NAME = "name"

class FlugCategories:
    _categoryConfigPath: dict = None             # store the category config path
    categoryConfig: FlugConfig.FlugConfig = None # store the actual category config (FlugConfig instance)

    def __init__(self, categoryConfigPath: str):
        self._categoryConfigPath = categoryConfigPath

        return

    def loadCfg(self) -> bool:
        # load the config file
        self.categoryConfig = FlugConfig.FlugConfig(self._categoryConfigPath)

        if self.categoryConfig.load() != True:
            logging.critical("Failed to load Category-Config from '%s'!" % self._categoryConfigPath)

            return False

        logging.info("Category-Config loaded! It has %d entries!" % len(self.categoryConfig.c().keys()))

        return True

    def save(self) -> bool:
        # save the config file
        if self.categoryConfig.save() != True:
            logging.critical("Failed to save Category-Config to '%s'!" % self._categoryConfigPath)

            return False

        return True

    def isConfigLoaded(self) -> bool:
        return self.categoryConfig != None

    def isCategoryKnown(self, id: str) -> bool:
        return self.categoryConfig.c().get(id, None) != None

    def getCategoryConfig(self, id: str) -> dict:
        return self.categoryConfig.c().get(id, None)

    def getCategoryName(self, id: str) -> str:
        cfg = self.getCategoryConfig(id)

        if cfg == None:
            return None
        
        return cfg.get(DEFAULT_FLUGVOGEL_CFG_KEY_CATEGORIES_NAME)

    def getTicketCategoryId(self):
        #get the catgoryID for the ticket category
        categoryId = self.getCategoryConfig(DEFAULT_FLUGVOGEL_CFG_KEY_CATEGORIES_TICKETS)

        if categoryId == None:
            return None

        return int(categoryId)

