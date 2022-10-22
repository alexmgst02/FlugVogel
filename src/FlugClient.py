#
# Implement the Discord Client for FlugVogel
#
import discord
import logging

import typing

glob = None

class FlugClient(discord.Client):
    guildId: discord.Object = None # Store the GuildID we're operating for
    subscribers: dict = {}         # Store functions describing to events 

    def __init__(self, *, intents: discord.Intents, guildId : discord.Object):
        super().__init__(intents = intents)

        self.guildID = guildId
        glob = self

        self.tree = discord.app_commands.CommandTree(self)
        
        #error handling
        @self.tree.error
        async def on_test_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
            if isinstance(error, discord.app_commands.CommandOnCooldown):
                await interaction.response.send_message(f"Nicht so schnell🚔! Versuche es in {error.retry_after} Sekunden erneut.", ephemeral=True)

    # this function is called by the client internally - don't touch
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=self.guildID)
        await self.tree.sync(guild=self.guildID)




    def subscribeTo(self, eventName: str) -> typing.Callable[[typing.Coroutine], typing.Coroutine]:
        def decorator(func: typing.Coroutine) -> typing.Coroutine:
            self.addSubscriber(eventName, func)

            return func

        return decorator

    def addSubscriber(self, eventName: str, coroutine: typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, typing.Any]]):
        # get a reference to the subscribers array
        subscribers = self.subscribers

        # check if this event is already known
        if self.subscribers.get(eventName, None) == None:
            # add an entry into the subscriber table
            self.subscribers.update({
                eventName: []
            })

            async def tfn(*args):
                for subscriber in subscribers.get(eventName):
                    await subscriber(*args)

            # define an event which executes the subscribers
            setattr(self, eventName, tfn)

        # add to the subscriber list
        self.subscribers.get(eventName).append(coroutine)
