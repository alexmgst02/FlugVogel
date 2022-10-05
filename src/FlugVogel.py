#
# FlugVogel Bot
#

import random
import FlugConfig
import FlugLoggerConfig
import FlugCredentials
import FlugClient
import logging

# default locations for the config and token file
DEFAULT_FLUGVOGEL_CONFIG_PATH = "config.json"
DEFAULT_FLUGVOGEL_TOKEN_PATH = "token.json"

# default config keys for the main application
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG = "logConfig"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FORMAT = "logFormat"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE = "logFile"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE_SIZE = "logFileSize"
DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE_NUM = "logFileNum"

class FlugVogel:
    version: str = None                           # The Version of the FlugVogel
    simulate: bool = None                         # Simulate/log commands, but don't execute them
    cfgPath : str = None                          # Path to the config file
    tokenPath : str = None                        # Path to the token file
    cfg : FlugConfig.FlugConfig = None            # FlugConfig instance
    creds: FlugCredentials.FlugCredentials = None # FlugCredentials instance
    _initSuccess = False # Set to `True` once initialization succeeded

    def __init__(self, version: str, configPath: str = DEFAULT_FLUGVOGEL_CONFIG_PATH, tokenPath: str = DEFAULT_FLUGVOGEL_TOKEN_PATH):
        # set up the logger
        FlugLoggerConfig.FlugLoggerConfig.init()

        # set file paths
        self.cfgPath = configPath
        self.tokenPath = tokenPath

        # load the config
        self.cfg = FlugConfig.FlugConfig(self.cfgPath)
        if not self.cfg.load():
            logging.critical("Failed to load FlugVogel-Config!")

            return
        
        #set logger again with config
        logCfg = self.cfg.getCfgObj()[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG]
        FlugLoggerConfig.FlugLoggerConfig.init(
            logFmt=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FORMAT],
            logFile=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE],
            logFileSize=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE_SIZE],
            logFileNum=logCfg[DEFAULT_FLUGVOGEL_CFG_KEY_LOG_CONFIG_FILE_NUM]
        )

        # load the credentials
        self.creds = FlugCredentials.FlugCredentials(self.tokenPath)
        
        if not self.creds.load():
            logging.critical("Failed to load FlugVogel-Credentials!")

            return

        # made it here; success
        self._initSuccess = True

        return

    def initWasSuccess(self) -> bool:
        """Check whether initialization succeeded.

        Returns `True` if initialization was a success, `False` otherwise. (`bool`)
        """
        return self._initSuccess

    def flieg(self):
        # check whether initialization worked
        if not self.initWasSuccess():
            logging.critical("Initialization didn't succeed! I refuse to flieg!")

            return

        logging.info("Hallo")
        logging.warning("Warning")
        logging.debug("Debug")

        intents = FlugClient.discord.Intents.default()
        client = FlugClient.FlugClient(intents=intents, guildId=FlugClient.discord.Object(id=1026808694773649449))


        @client.event
        async def on_ready():
            print(f'Logged in as {client.user} (ID: {client.user.id})')
            print('------')


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


        client.run(self.creds.getToken())

if __name__ == "__main__":
    vogel = FlugVogel("0.0.1",
        configPath=DEFAULT_FLUGVOGEL_CONFIG_PATH,
        tokenPath=DEFAULT_FLUGVOGEL_TOKEN_PATH)

    vogel.flieg()
