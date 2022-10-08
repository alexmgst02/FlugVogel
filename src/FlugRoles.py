#
# Role Information Handling
#
import FlugConfig
import logging

DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_ASSIGNABLE = "assignable"
DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_NAME = "name"
DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_DEACTIVATED = "banned"


class FlugRoles:
    _roleConfigPath: dict = None             # store the role config path
    roleConfig: FlugConfig.FlugConfig = None # store the actual role config (FlugConfig instance)

    def __init__(self, roleConfigPath: str):
        self._roleConfigPath = roleConfigPath

        return

    def loadCfg(self) -> bool:
        # load the config file
        self.roleConfig = FlugConfig.FlugConfig(self._roleConfigPath, backup=True)

        if self.roleConfig.load() != True:
            logging.critical("Failed to load Role-Config from '%s'!" % self._roleConfigPath)

            return False

        logging.info("Role-Config loaded! It has %d entries!" % len(self.roleConfig.c().keys()))

        return True

    def save(self) -> bool:
        # save the config file
        if self.roleConfig.save() != True:
            logging.critical("Failed to save Role-Config to '%s'!" % self._roleConfigPath)

            return False

        return True

    def isConfigLoaded(self) -> bool:
        return self.roleConfig != None

    def isRoleKnown(self, id: str) -> bool:
        return self.roleConfig.c().get(id, None) != None

    def getRoleConfig(self, id: str) -> dict:
        return self.roleConfig.c().get(id, None)

    def getRoleID(self, name: str) -> int:
        # go through all role configs
        for key, config in self.roleConfig.c().items():
            if config.get(DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_NAME, None) == name:
                return int(key)

        return None

    def isRoleAssignable(self, id: str) -> bool:
        if self.isRoleKnown(id) and self.getRoleConfig(id).get(DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_ASSIGNABLE, False) == True:
            return True
        return False

    def getDeactivationRole(self) -> int:
        return self.getRoleConfig(DEFAULT_FLUGVOGEL_CFG_KEY_ROLES_DEACTIVATED).get("id", None)