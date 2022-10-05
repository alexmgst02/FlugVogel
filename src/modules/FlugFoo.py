import logging
import random

import FlugChannels
import FlugRoles
import FlugUsers
import FlugClient
import FlugConfig

def init(name: str, configFile: str, 
        client: FlugClient.FlugClient,
        channels: FlugChannels.FlugChannels,
        users: FlugUsers.FlugUsers,
        roles: FlugRoles.FlugRoles):
    # greet-message
    logging.info("I am '%s'! I go initialized with the config file '%s'!" % (name, configFile))
    
    @client.event
    async def on_ready():
        print(f'Logged in as {client.user} (ID: {client.user.id})')
        print('------')

    @client.event
    async def on_message(message: FlugClient.discord.Message):
        id = str(message.channel.id)

        if channels.isChannelKnown(id):
            channel = channels.getchannelConfig(id)
            
            if channel.get("isPolitical") == True:
                logging.info("Reacting to a political message in '%s'!" % message.channel.name)

                if message.author.id == 580306587156217856:
                    await message.add_reaction("🤝")
                elif message.author.id == 282908150993125376:
                    await message.add_reaction("🐟")
                else:
                    await message.add_reaction("<:9462pepe9:1026820740403695646>")
        else:
            logging.info("Message (%s) from unknown channel '%s' (%s)!" % (message.content, id, message.channel.name))

    @client.tree.command()
    async def hello(interaction: FlugClient.discord.Interaction):
        """Says hello!"""
        await interaction.response.send_message(f'Hi, {interaction.user.mention}')


    @client.tree.command()
    @FlugClient.discord.app_commands.describe(
        first_value='The first value you want to add something to',
        second_value='The value you want to add to the first value',
    )
    async def add(interaction: FlugClient.discord.Interaction, first_value: float, second_value: float):
        """Adds two numbers together."""
        await interaction.response.send_message(f'{first_value} + {second_value} = {first_value + second_value}')

    # The rename decorator allows us to change the display of the parameter on Discord.
    # In this example, even though we use `text_to_send` in the code, the client will use `text` instead.
    # Note that other decorators will still refer to it as `text_to_send` in the code.
    @client.tree.command()
    @FlugClient.discord.app_commands.rename(text_to_send='text')
    @FlugClient.discord.app_commands.describe(text_to_send='Text to send in the current channel')
    async def send(interaction: FlugClient.discord.Interaction, text_to_send: str):
        """Sends the text into the current channel."""
        await interaction.response.send_message("HA! NOOOPE! Copium für Dich mein Guter! <:9462pepe9:1026820740403695646>")


    # To make an argument optional, you can either give it a supported default argument
    # or you can mark it as Optional from the typing standard library. This example does both.
    @client.tree.command()
    @FlugClient.discord.app_commands.describe(member='The member you want to get the joined date from; defaults to the user who uses the command')
    async def joined(interaction: FlugClient.discord.Interaction, member: FlugClient.discord.Member = None):
        """Says when a member joined."""
        # If no member is explicitly provided then we use the command user here
        member = member or interaction.user

        # The format_dt function formats the date time into a human readable representation in the official client
        await interaction.response.send_message(f'{member} joined {FlugClient.discord.utils.format_dt(member.joined_at)}')


    # A Context Menu command is an app command that can be run on a member or on a message by
    # accessing a menu within the client, usually via right clicking.
    # It always takes an interaction as its first parameter and a Member or Message as its second parameter.

    # This context menu command only works on members
    @client.tree.context_menu(name='Show Join Date')
    async def show_join_date(interaction: FlugClient.discord.Interaction, member: FlugClient.discord.Member):
        # The format_dt function formats the date time into a human readable representation in the official client
        await interaction.response.send_message(f'{member} joined at {FlugClient.discord.utils.format_dt(member.joined_at)}')


    # This context menu command only works on messages
    @client.tree.context_menu(name='Report to Moderators')
    async def report_message(interaction: FlugClient.discord.Interaction, message: FlugClient.discord.Message):
        # We're sending this response message with ephemeral=True, so only the command executor can see it
        await interaction.response.send_message(
            f'Thanks for reporting this message by {message.author.mention} to our moderators.', ephemeral=True
        )

        # Handle report by sending it into a log channel
        log_channel = interaction.guild.get_channel(0)  # replace with your channel id

        embed = FlugClient.discord.Embed(title='Reported Message')
        if message.content:
            embed.description = message.content

        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.timestamp = message.created_at

        url_view = FlugClient.discord.ui.View()
        url_view.add_item(FlugClient.discord.ui.Button(label='Go to Message', style=FlugClient.discord.ButtonStyle.url, url=message.jump_url))

        await log_channel.send(embed=embed, view=url_view)
