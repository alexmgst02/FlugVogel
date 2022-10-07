import logging
import random

import discord

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugRoles
import FlugUsers
import FlugConfig

class FlugDicegame(modules.FlugModule.FlugModule):
    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))
        
    def setup(self):
        # setup the dice game
        @self.client.tree.command()
        @discord.app_commands.describe(
            first_value='I don\'t care about what you type here, big L, go cope, lol'
        )
        async def dicegame(interaction: discord.Interaction, first_value: str):
            """Plays a fair game of dice."""
            member = interaction.user

            if member.id == 580306587156217856: #lx00t
                r1 = random.randint(1,5)
                resp = "I rolled a %d. You got a %d. Fair game, loser! 🤝" % (r1, r1 - 4)
            else:
                r1 = random.randint(2,6)
                resp = "I rolled a %d. You got a %d. Lol, how can you be _that_ bad? <a:pepemeltdown:1026820761840783381>" % (r1, r1 - 1)

            await interaction.response.send_message(resp)

        @self.client.subscribeTo('on_message')
        async def meltdown(message: discord.Message):
            if message.author.id == self.client.user.id:
                return

            if "rigged" in message.content.lower():
                await message.add_reaction("<a:pepemeltdown:1026820761840783381>")
                await message.reply("Ich bin based, nicht rigged <:Clueless:1026820743985643550>")

        @self.client.subscribeTo('on_message')
        async def pong(message: discord.Message):
            if "ping" in message.content.lower():
                await message.reply("pong")

        @self.client.subscribeTo('on_message_edit')
        async def deedit(before: discord.Message, after: discord.Message):
            await after.reply(f"Das habe ich gesehen! Hier ist das original dieser Nachricht: {before.content}")

        @self.client.subscribeTo('on_message_edit')
        async def deedit(before: discord.Message, after: discord.Message):
            await after.add_reaction("<a:pepemeltdown:1026820761840783381>")

        return True

CLASS = FlugDicegame
