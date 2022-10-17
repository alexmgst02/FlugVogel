#
# FlugModule class - Should be used as base class for all modules in modules/
#
import FlugCategories
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig

class FlugModule:
    moduleName: str = None
    configFilePath: str = None
    client: FlugClient.FlugClient = None
    channels: FlugChannels.FlugChannels = None
    roles: FlugRoles.FlugRoles = None
    users: FlugUsers.FlugUsers = None
    categories: FlugCategories.FlugCategories = None
    config: FlugConfig.FlugConfig = None


    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None,
            categories: FlugCategories.FlugCategories = None):
        self.moduleName = moduleName
        self.configFilePath = configFilePath
        self.client = client
        self.channels = channels
        self.roles = roles
        self.users = users
        self.categories = categories
    def setup(self):
        raise NotImplementedError("The setup function must be implemented!")
