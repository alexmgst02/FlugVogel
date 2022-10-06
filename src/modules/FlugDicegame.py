import logging
import random

import FlugChannels
import FlugRoles
import FlugUsers
import FlugClient
import FlugConfig

def init(name: str, configFile: str, 
        client: FlugClient.FlugClient,
        channelConfig: FlugChannels.FlugChannels,
        userConfig: FlugUsers.FlugUsers,
        roleConfig: FlugRoles.FlugRoles):
    # greet-message
    logging.info("I am '%s'! I got initialized with the config file '%s'!" % (name, configFile))

    # setup the dice game
    @client.tree.command()
    @FlugClient.discord.app_commands.describe(
        first_value='I don\'t care about what you type here, big L, go cope, lol'
    )
    async def dicegame(interaction: FlugClient.discord.Interaction, first_value: str):
        """Plays a fair game of dice."""
        member = interaction.user

        if member.id == 580306587156217856: #lx00t
            r1 = random.randint(1,5)
            resp = "I rolled a %d. You got a %d. Fair game, champ! 🤝" % (r1, r1 + 1)
        else:
            r1 = random.randint(2,6)
            resp = "I rolled a %d. You got a %d. Lol, how can you be _that_ bad? <a:pepemeltdown:1026820761840783381>" % (r1, r1 - 1)

        await interaction.response.send_message(resp)
