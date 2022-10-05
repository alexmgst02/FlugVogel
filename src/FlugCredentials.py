#
# Handle Credentials for FlugVogel
# This is NOT in any shape or form secure.
# It loads credentials from a json file.
#
import logging
import json

# controls the json-key inspected to have the auth token
DEFAULT_FLUGVOGEL_AUTHTOKEN_KEY = "token"

class FlugCredentials:
    ##### Class Initialization Parameters ####
    credPath: str = None # Path to the Credentials file

    ##### Class Internal Variables #####
    _credsObj: dict = None # Contents of the Credentials File as dict

    def __init__(self, credPath: str):
        """Initialize an instance of FlugCredentials.

        `credFile` File to load the Credentials from. (`str`)
        """
        self.credPath = credPath

    def load(self) -> bool:
        """Load the contents of the credentials file

        Returns `True` on success, `False` on failures. (`bool`)
        """
        # read the creds file
        try:
            with open(self.credPath, "r") as fd:
                self._credsObj = json.load(fd)
        except Exception as e:
            logging.critical("Failed to load credentials from '%s'!" % self.credPath)
            logging.exception(e)
            return False

        return True

    def getToken(self) -> str:
        """Get the Authentication Token from the loaded credentials

        Returns `None` if the credentials aren't loaded or the token. (`str`)
        """
        if self._credsObj == None:
            return None

        return self._credsObj.get(DEFAULT_FLUGVOGEL_AUTHTOKEN_KEY, None)
