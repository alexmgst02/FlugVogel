#
# Implement the Discord Client for FlugVogel
#
import discord

class FlugClient(discord.Client):
    guildId: discord.Object = None

    def __init__(self, *, intents: discord.Intents, guildId : discord.Object):
        super().__init__(intents = intents)

        self.guildID = guildId

        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=self.guildID)
        await self.tree.sync(guild=self.guildID)
