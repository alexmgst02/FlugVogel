import logging

import FlugChannels
import FlugRoles
import FlugUsers
import FlugClient
import FlugConfig
from discord.utils import get



def init(name: str, configFile: str,
        client: FlugClient.FlugClient,
        channels: FlugChannels.FlugChannels,
        users: FlugUsers.FlugUsers,
        roles: FlugRoles.FlugRoles):
    # greet-message
    logging.info("I am '%s'! I go initialized with the config file '%s'!" % (name, configFile))

    cfg = FlugConfig.FlugConfig(cfgPath=configFile)

    if cfg.load() != True:
        logging.critical(f"Could not load config for {name}")
        return
    else:
        logging.info(f"Config File for {name} has been loaded")

    cfgObj = cfg.c()
    deleteTimer = cfgObj.get("messageDeleteTimer")

    #When no logChannel is configured the module will shut down
    logChannel = None
    logChannelId = channels.getLogChannelId()
    if logChannelId == 0:
        logging.critical(f"{name} shutting down")
        return
    
    @client.event
    async def on_ready():
        logChannel = client.get_channel(logChannelId)
        if logChannel == None:
            logging.critical(f"{name} could not find logChannel. ")
              
    
    
    @client.event   
    async def on_message(message):
        logChannel = client.get_channel(logChannelId)
        channelId = str(message.channel.id)
        
        # are we in the correct text channel?
        if message.author != client.user and channels.isChannelRoleHandling(channelId):
           # are we allowed to assign a role? 
           authorId = str(message.author.id)
           if users.isUserDeactivated(authorId):
               logging.warning("Banned user has breached role adding channel. Action required.")
               await logChannel.send(f"Banned user {message.author.mention} has breached role adding channel. Action required.")
               
           else:
    
               # have we entered an existing role name?
               role = get(message.guild.roles, name=message.content)
               if role != None:
                   
                   roleId = str(role.id)
                   
                   # is the role allowed to be assigned?
                   if roles.isRoleAssignable(roleId):
                       await message.author.add_roles(role)
                       await logChannel.send(f"{message.author.mention} assigned role {role.name}")
                       
                   else:
                       await message.channel.send(f"Die Rolle {role.name} ist nicht assignable. {message.author.mention}", delete_after=deleteTimer)

               else:
                   logging.warning(f"Role could not be assigned {message.content}")
                   await message.channel.send(f"Bitte so schreiben wie oben angegeben. {message.author.mention}", delete_after=deleteTimer)
                   await logChannel.send(f"{message.author.mention} tried to assign {message.content}")

           await message.delete()
