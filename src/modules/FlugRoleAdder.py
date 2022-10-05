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
    deleteTimer = cfgObj.get("messageDeleteCounter")

    
    logChannelId = channels.getChannelConfig("log").get("id")
    
    
    
    @client.event   
    async def on_message(message):
        print(logChannelId)
        logChannel = client.get_channel(1026808696556236852)
        channelId = str(message.channel.id)
        # are we in the correct text channel?
        
        if message.author != client.user and channels.isChannelKnown(channelId) and channels.getChannelConfig(channelId).get("RoleHandling"):
           # are we allowed to assign a role? 
           authorId = str(message.author.id)
           
           if users.isUserKnown(authorId) and users.getUserConfig(authorId).get("banned"):
               logging.warning("Banned user has breached role adding channel. Action required")
               await logChannel.send(f"Banned user {message.author.mention} has breached role adding channel. Action required")
               
           else:
    
               # have we entered an existing role name?
               try:
                   role = get(message.guild.roles, name=message.content)
                   roleId = str(role.id)
                   
                   # is the role allowed to be assigned?
                   if roles.isRoleKnown(roleId) and roles.getRoleConfig(roleId).get("assignable"):
                       await message.author.add_roles(role)
                       await logChannel.send(f"{message.author.mention} assigned role {role.name}")
                       
                   else:
                       await message.channel.send(f"Die Rolle {role.name} ist nicht assignable", delete_after=deleteTimer)

               except Exception as e:
                   logging.warning(f"Role could not be assigned {e}")
                   await message.channel.send(f"Bitte so schreiben wie oben angegeben. {message.author.mention}", delete_after=deleteTimer)
                   await logChannel.send(f"{message.author.mention} tried to assign {message.content}")      
