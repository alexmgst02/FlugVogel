#
# A class to represent simple permissions for commands/requests/...
#
import logging
import typing
import discord

import FlugRoles
import FlugUsers

import util.isInList

FLUG_PERMISSIONS_CFG_DEFAULT_ALLOW = "defaultAllow"
FLUG_PERMISSIONS_CFG_DEFAULT_TARGET_ALLOW = "defaultTargetAllow"
FLUG_PERMISSIONS_CFG_MEMBER_ALLOW_LIST = "memberAllowlist"
FLUG_PERMISSIONS_CFG_MEMBER_BLOCK_LIST = "memberBlocklist"
FLUG_PERMISSIONS_CFG_ROLE_ALLOW_LIST = "roleAllowlist"
FLUG_PERMISSIONS_CFG_ROLE_BLOCK_LIST = "roleBlocklist"
FLUG_PERMISSIONS_CFG_TARGET_MEMBER_ALLOW_LIST = "targetMemberAllowlist"
FLUG_PERMISSIONS_CFG_TARGET_MEMBER_BLOCK_LIST = "targetMemberBlocklist"
FLUG_PERMISSIONS_CFG_TARGET_ROLE_ALLOW_LIST = "targetRoleAllowlist"
FLUG_PERMISSIONS_CFG_TARGET_ROLE_BLOCK_LIST = "targetRoleBlocklist"

class FlugPermissions:
    permissionsDict: dict = {}
    roles: FlugRoles.FlugRoles = None
    members: FlugUsers.FlugUsers = None

    ###############################################################
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
    #@               DO NOT CHANGE ORDER OR VALUES               @#
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
    ###############################################################
    CAN_DO_CMD_UNKNOWN = 0 # Command is unknown
    CAN_DO_HARD_NO = 1     # Command can't be done - Explicitly set (by role or member)
    CAN_DO_WEAK_NO = 2     # Command can't be done - Determined by default setting
    CAN_DO_WEAK_YES = 3    # Command can be done - Determined by default setting
    CAN_DO_HARD_YES = 4    # Command can be done - Explicitly set (by role or member)

    CAN_DO_STRINGS = ["CAN_DO_CMD_UNKNOWN", "CAN_DO_HARD_NO", "CAN_DO_WEAK_NO", "CAN_DO_WEAK_YES", "CAN_DO_HARD_YES"]

    def __init__(self, permissionsDict: dict, roles: FlugRoles.FlugRoles, members: FlugUsers.FlugUsers):
        """Constructor for the FlugPermissions class

        This constructor only takes on parameter - a `dict`. All fields except `defaultAllow` 
        and `defaultTargetAllow` are optional. "can('t)" is used as "is(n't) allowed to".

        ```json
        {
            "exampleCommandName": {            /* Starts the Permissions Block for a command */
                "defaultAllow": true,          /* true: members can execute the command unless specified otherwise by a blocklist */
                "defaultTargetAllow": true,    /* true: members can be targeted by the command unless specified otherwise by a blocklist */
                "memberAllowlist": [],       /* memberIDs that can use the command - ignored if defaultAllow is true */
                "memberBlocklist": [],       /* memberIDs that can't use the command - ignored if defaultAllow is false */
                "roleAllowlist": [],         /* RoleIDs that can use the command - ignored if defaultAllow is true */
                "roleBlocklist": [],         /* ROleIDs that can't use the command - ignored if defaultAllow is false */
                "targetMemberAllowlist": [], /* memberIDs that can be targeted by the command - ignored if defaultTargetAllow is true */
                "targetMemberBlocklist": [], /* memberIDs that can't be targeted by the command - ignored if defaultAllow is false */
                "targetRoleAllowlist": [],   /* RoleIDs that can be targeted by the command - ignored if defaultTargetAllow is true */
                "targetRoleBlocklist": [],   /* RoleIDs that can't be targeted by the command - ignored if defaultAllow is false */
            }
        }
        ```
        User setting overwrites roles setting overwrites default setting.

        `roles` (`FlugRoles.FlugRoles`) and `members` (`FlugUsers.FlugUsers`) are needed to revolve Member/Role names to IDs.
        """
        self.roles = roles
        self.members = members

        # go through the config, make sure defaults are set
        for command, config in permissionsDict.items():
            # add the command entry
            self.permissionsDict.update({command: {}})

            # make sure the defaults are set
            if config.get(FLUG_PERMISSIONS_CFG_DEFAULT_ALLOW, None) == None or config.get(FLUG_PERMISSIONS_CFG_DEFAULT_TARGET_ALLOW, None) == None:
                logging.critical(
                    "Mandatory fields (%s or %s) missing in permissionsDict for command '%s'!" % 
                    (FLUG_PERMISSIONS_CFG_DEFAULT_ALLOW, FLUG_PERMISSIONS_CFG_DEFAULT_TARGET_ALLOW, command)
                )

                raise ValueError(
                    "Mandatory fields (%s or %s) missing in permissionsDict for command '%s'!" % 
                    (FLUG_PERMISSIONS_CFG_DEFAULT_ALLOW, FLUG_PERMISSIONS_CFG_DEFAULT_TARGET_ALLOW, command)
                )

            # copy the defaults
            self.permissionsDict.get(command).update({
                FLUG_PERMISSIONS_CFG_DEFAULT_ALLOW: config.get(FLUG_PERMISSIONS_CFG_DEFAULT_ALLOW),
                FLUG_PERMISSIONS_CFG_DEFAULT_TARGET_ALLOW: config.get(FLUG_PERMISSIONS_CFG_DEFAULT_TARGET_ALLOW)
            })

            # translate the member lists
            for listKey in [FLUG_PERMISSIONS_CFG_MEMBER_ALLOW_LIST, FLUG_PERMISSIONS_CFG_MEMBER_BLOCK_LIST,
                            FLUG_PERMISSIONS_CFG_TARGET_MEMBER_ALLOW_LIST, FLUG_PERMISSIONS_CFG_TARGET_MEMBER_BLOCK_LIST]:
                tmp = self.__memberNameList2IDList__(permissionsDict.get(command).get(listKey))

                if tmp == None:
                    logging.critical("Failed to translate UserName list into UserID list!")
                    
                    raise ValueError("Failed to translate UserName list into UserID list!")

                self.permissionsDict.get(command).update({listKey: tmp})
                
            # translate the role lists
            for listKey in [FLUG_PERMISSIONS_CFG_ROLE_ALLOW_LIST, FLUG_PERMISSIONS_CFG_ROLE_BLOCK_LIST,
                            FLUG_PERMISSIONS_CFG_TARGET_ROLE_ALLOW_LIST, FLUG_PERMISSIONS_CFG_TARGET_ROLE_BLOCK_LIST]:
                tmp = self.__roleNameList2IDList__(permissionsDict.get(command).get(listKey))

                if tmp == None:
                    logging.critical("Failed to translate RoleName list into RoleID list!")
                    
                    raise ValueError("Failed to translate RoleName list into RoleID list!")

                self.permissionsDict.get(command).update({listKey: tmp})

        logging.debug("Loaded and translated permissionsDict: %s" % str(self.permissionsDict))
            
    def __memberNameList2IDList__(self, nameList: typing.List[str]) -> typing.List[str]:
        out = []

        if nameList == None:
            return out

        # translate each name to an id
        for name in nameList:
            id = self.members.getUserID(name)

            # fail if a name can't be translated
            if (id == None):
                logging.critical("Permissions Config contains an unknown username: '%s'!" % name)

                return None

            out.append(str(id))

        return out

    def __roleNameList2IDList__(self, nameList: typing.List[str]) -> typing.List[str]:
        out = []

        if nameList == None:
            return out

        # translate each name to an id
        for name in nameList:
            id = self.roles.getRoleID(name)

            # fail if a name can't be translated
            if (id == None):
                logging.critical("Permissions Config contains an unknown rolename: '%s'!" % name)

                return None

            out.append(str(id))

        return out

    def setPermissionsDict(self, newPermissionsDict: dict):
        self.permissionsDict = newPermissionsDict

    def getPermissionsDict(self) -> dict:
        return self.permissionsDict

    def isCommandKnown(self, commandName: str) -> bool:
        """Check whether a command is present in the permissions dictionary

        `commandName` Name of the command to check for (`str`)
        """
        return self.permissionsDict.get(commandName, False) != False

    def __canDoGeneric__(self, commandName: str, id: int, blockListKey: str, defaultAllowKey: str, allowListKey: str) -> int:
        """Generic "canDo" checker

        `commandName` Command name to check for (`str`)

        `id` ID to check for; what kind of ID it has to be is determined by the lists checked against (`str`)

        `blockListKey` They key of the block list to check against in the permissions dictionary (`str`)

        `defaultAllowKey` They key of the default allow value to check against in the permissions dictionary (`str`)

        `allowListKey` They key of the allow list to check against in the permissions dictionary (`str`)

        Returns `FlugPermissions.CAN_DO*`.
        """

        # check whether the command is known
        if not self.isCommandKnown(commandName):
            logging.warning("Can't look up permissions for unknown command '%s'!" % commandName)

            return self.CAN_DO_CMD_UNKNOWN

        # check whether the role id is on a blocklist
        if util.isInList.isInList(str(id), self.permissionsDict.get(commandName).get(blockListKey, None)):
            return self.CAN_DO_HARD_NO

        # check whether the action is allowed by default
        if self.permissionsDict.get(commandName).get(defaultAllowKey) == True:
            return self.CAN_DO_WEAK_YES

        # check whether the role is in an explicit allow list
        if util.isInList.isInList(str(id), self.permissionsDict.get(commandName).get(allowListKey, None)):
            return self.CAN_DO_HARD_YES
        
        return self.CAN_DO_WEAK_NO

    def canRoleDo(self, commandName: str, role: discord.Role) -> int:
        """Checks whether a role is allowed to execute a given command
        
        `commandName` Name of the command to check for (`str`)

        `role` Role to check for (`discord.Role`)

        Returns `FlugPermissions.CAN_DO*`.
        """
        return self.__canDoGeneric__(commandName, role.id,
            FLUG_PERMISSIONS_CFG_ROLE_BLOCK_LIST,
            FLUG_PERMISSIONS_CFG_DEFAULT_ALLOW,
            FLUG_PERMISSIONS_CFG_ROLE_ALLOW_LIST
        )

    def canRoleBeTargeted(self, commandName: str, role: discord.Role) -> int:
        """Checks whether a role is allowed to be targeted by a given command
        
        `commandName` Name of the command to check for (`str`)

        `role` Role to check for (`discord.Role`)

        Returns `FlugPermissions.CAN_DO*`.
        """
        return self.__canDoGeneric__(commandName, role.id,
            FLUG_PERMISSIONS_CFG_TARGET_ROLE_BLOCK_LIST,
            FLUG_PERMISSIONS_CFG_DEFAULT_TARGET_ALLOW,
            FLUG_PERMISSIONS_CFG_TARGET_ROLE_ALLOW_LIST
        )

    def canRolesDo(self, commandName: str, roles: typing.List[discord.Role]) -> int:
        """Checks whether every role in a list is allowed to execute a given command
        
        `commandName` Name of the command to check for (`str`)

        `roles` List of roles to check for (`typing.List[discord.Role]`)

        Returns `FlugPermissions.CAN_DO*`.
        """
        ret = self.CAN_DO_HARD_YES

        for role in roles:
            r = self.canRoleDo(commandName, role)

            # return if the command is unknown
            if r == self.CAN_DO_CMD_UNKNOWN:
                return r

            # use it if it's smaller than the current one
            ret = r if r < ret else ret

        return ret

    def canRolesBeTargeted(self, commandName: str, roles: typing.List[discord.Role]) -> int:
        """Checks whether every role in a list is allowed to to be targeted by a given command
        
        `commandName` Name of the command to check for (`str`)

        `roles` List of roles to check for (`typing.List[discord.Role]`)

        Returns `FlugPermissions.CAN_DO*`.
        """
        ret = self.CAN_DO_HARD_YES

        for role in roles:
            r = self.canRoleBeTargeted(commandName, role)

            # return if the command is unknown
            if r == self.CAN_DO_CMD_UNKNOWN:
                return r

            # use it if it's smaller than the current one
            ret = r if r < ret else ret

        return ret

    def canMemberDo(self, commandName: str, member: discord.Member, checkRoles: bool = True) -> int:
        """Checks whether a member is allowed to execute a given command
        
        `commandName` Name of the command to check for (`str`)

        `member` Member to check for (`discord.Role`)

        `checkRoles` If set to `True`, it will suffice if one of the roles
        the member has is allowed to execute the command. Defaults to `True` (`bool`)

        Returns `FlugPermissions.CAN_DO*`.
        """
        # first check the member directly
        r = self.__canDoGeneric__(commandName, member.id,
            FLUG_PERMISSIONS_CFG_MEMBER_BLOCK_LIST,
            FLUG_PERMISSIONS_CFG_DEFAULT_ALLOW,
            FLUG_PERMISSIONS_CFG_MEMBER_ALLOW_LIST
        )

        # return if there is a hard answer
        if r == self.CAN_DO_HARD_YES or r == self.CAN_DO_HARD_NO or r == self.CAN_DO_CMD_UNKNOWN:
            return r

        # check the groups
        if checkRoles:
            return self.canRolesDo(commandName, member.roles)

        return r

    def canMemberBeTargeted(self, commandName: str, member: discord.Member, checkRoles: bool = True) -> int:
        """Checks whether a member is allowed to be targeted by a given command
        
        `commandName` Name of the command to check for (`str`)

        `role` Member to check for (`discord.Role`)

        `checkRoles` If set to `True`, it will suffice if one of the roles
        the member has is allowed to be targeted by the command. Defaults to `True` (`bool`)

        Returns `FlugPermissions.CAN_DO*`.
        """
        # first check the member directly
        r = self.__canDoGeneric__(commandName, member.id,
            FLUG_PERMISSIONS_CFG_TARGET_MEMBER_BLOCK_LIST,
            FLUG_PERMISSIONS_CFG_DEFAULT_TARGET_ALLOW,
            FLUG_PERMISSIONS_CFG_TARGET_MEMBER_ALLOW_LIST
        )

        # return if there is a hard answer
        if r == self.CAN_DO_HARD_YES or r == self.CAN_DO_HARD_NO or r == self.CAN_DO_CMD_UNKNOWN:
            return r

        # check the groups
        if checkRoles:
            return self.canRolesBeTargeted(commandName, member.roles)

        return r

    def canDo(self, commandName: str, activeMember: discord.Member, targetMember: discord.Member) -> int:
        """Cheks whether a command can be executed by a member with a given target

        Returns `FlugPermissions.CAN_DO*`.
        """
        r1 = r2 = FlugPermissions.CAN_DO_HARD_YES

        if activeMember != None:
            r1 = self.canMemberDo(commandName, activeMember, checkRoles=True)

        if targetMember != None:
            r2 = self.canMemberBeTargeted(commandName, targetMember, checkRoles=True)

        return (r1 if r1 < r2 else r2)
