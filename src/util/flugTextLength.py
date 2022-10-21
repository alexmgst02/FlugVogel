DEFAULT_DISCORD_MAX_MESSAGE_LENGTH = 2000
DEFAULT_DISCORD_MAX_LABEL_LENGTH = 80
DEFAULT_FLUGVOGEL_MAX_ROLE_NAME_LENGTH = 150


def isMessageLengthValid(msg: str) -> bool:
    if len(msg) > DEFAULT_DISCORD_MAX_MESSAGE_LENGTH:
        return False

    return True

def isRoleNameLengthValid(name: str) -> bool:
    if len(name) > DEFAULT_FLUGVOGEL_MAX_ROLE_NAME_LENGTH:
        return False
    
    return True

def isLabelLengthValid(labelText: str) -> bool:
    if len(labelText) > DEFAULT_DISCORD_MAX_LABEL_LENGTH:
        return False
    
    return True