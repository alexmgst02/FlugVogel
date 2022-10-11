from math import perm
import FlugPermissions
import logging
import discord

import util.logHelper

async def canDoWrapper(commandName: str, user: discord.Member, target: discord.Member, permissions: FlugPermissions.FlugPermissions, logChannel: discord.TextChannel):
    # execute the request
    ret = permissions.canDo(commandName, user, target)

    # log on any deny, don't log on allow
    if ret == FlugPermissions.FlugPermissions.CAN_DO_CMD_UNKNOWN:
        await util.logHelper.logToChannelAndLog(logChannel, logging.CRITICAL, "⚠️ FlugPermissions - Unknown Command ⚠️",
            f"Got permissions request for unknown command `{commandName}` from {user.mention} ({user.id})" +
            f" towards {target.mention} ({target.id})!" if target != None else "!"
        )

        return False
    elif ret == FlugPermissions.FlugPermissions.CAN_DO_HARD_NO or ret == FlugPermissions.FlugPermissions.CAN_DO_WEAK_NO:
        await util.logHelper.logToChannelAndLog(logChannel, logging.WARNING, "⚔️ FlugPermissions - Illegal Request ⚔️",
            f"Got illegal permissions request for command `{commandName}` from {user.mention} ({user.id})" + (
            f" towards {target.mention} ({target.id})!" if target != None else "!")
        )

        return False
    else:
        return True