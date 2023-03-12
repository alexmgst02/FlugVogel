import asyncio
import logging
import typing
import datetime

import discord

import util.flugTextLength
import util.flugVoterHelper
import util.flugPermissionsHelper
import util.logHelper

import modules.FlugModule
import FlugClient
import FlugChannels
import FlugCategories
import FlugRoles
import FlugUsers
import FlugConfig
import FlugPermissions


DEFAULT_FLUGVOGEL_VOTER_CFG_MAX_VOTES = "maxVotes"
DEFAULT_FLUGVOGEL_VOTER_CFG_MAX_WAIT_TIME = "maxWaitTimeMinutes"

DEFAULT_FLUGVOGEL_VOTER_CFG_PERMISSIONS = "permissions"
DEFAULT_FLUGVOGEL_VOTER_CFG_PERMISSIONS_LONG_VOTE = "long_vote"
DEFAULT_FLUGVOGEL_VOTER_CFG_PERMISSIONS_MORE_VOTES  = "bypass_vote_count"


class FlugVoter(modules.FlugModule.FlugModule):
    cfg: FlugConfig.FlugConfig = None
    logChannelId : int = None
    logChannel : discord.abc.GuildChannel = None
    maxWaitTime : int = None
    maxVotes : int = None
    permissions : FlugPermissions.FlugPermissions = None
    voteCount : dict = None

    def __init__(self, moduleName: str, configFilePath: str,
            client: FlugClient.FlugClient = None,
            channels: FlugChannels.FlugChannels = None,
            roles: FlugRoles.FlugRoles = None, 
            users: FlugUsers.FlugUsers = None,
            categories: FlugCategories.FlugCategories = None):
        # setup the super class
        super().__init__(moduleName, configFilePath, client, channels, roles, users, categories)

        # greet-message
        logging.info("I am '%s'! I got initialized with the config file '%s'!" % (self.moduleName, self.configFilePath))
        
    async def get_log_channel_on_ready(self):
        self.logChannel = self.client.get_channel(self.logChannelId)

        if self.logChannel == None:
            logging.critical(f"'{self.moduleName}' could not find the log channel ({self.logChannelId})!")

    def setup(self):
        # load the module config
        self.cfg = FlugConfig.FlugConfig(cfgPath=self.configFilePath)

        if self.cfg.load() != True:
            logging.critical(f"Could not load config for '{self.moduleName}' from '{self.configFilePath}'!")

            return False
        else:
            logging.info(f"Config for '{self.moduleName}' has been loaded from '{self.configFilePath}'!")


        try:
            self.permissions = FlugPermissions.FlugPermissions(
                self.cfg.c().get(DEFAULT_FLUGVOGEL_VOTER_CFG_PERMISSIONS),
                self.roles, self.users
            )
        except Exception as e:
            logging.critical(f"Failed to setup permission config for {self.moduleName}!")
            logging.exception(e)

            return False

        self.maxVotes = self.cfg.c().get(DEFAULT_FLUGVOGEL_VOTER_CFG_MAX_VOTES)

        if self.maxVotes == None:
            logging.critical(f"Could not load {DEFAULT_FLUGVOGEL_VOTER_CFG_MAX_VOTES} for '{self.moduleName}' from '{self.configFilePath}'!")
            
            return False

        self.maxWaitTime = self.cfg.c().get(DEFAULT_FLUGVOGEL_VOTER_CFG_MAX_WAIT_TIME)

        if self.maxWaitTime == None:
            logging.critical(f"Could not load {DEFAULT_FLUGVOGEL_VOTER_CFG_MAX_WAIT_TIME} for '{self.moduleName}' from '{self.configFilePath}'!")
            
            return False

        self.logChannelId = self.channels.getChannelId(FlugChannels.DEFAULT_FLUGVOGEL_CFG_KEY_CHANNELS_LOG)

        if self.logChannelId == None:
            logging.critical(f"No ID found for the log-Channel '{self.moduleName}'!")

            return False

        self.voteCount = {}

        # register self.get_log_channel_on_ready for on_ready
        self.client.addSubscriber("on_ready", self.get_log_channel_on_ready)

        @discord.app_commands.rename(waitTime = "abstimmungszeit")
        @discord.app_commands.rename(content="inhalt")        
        @self.client.tree.command(description="Starten Sie eine Abstimmung.")
        @discord.app_commands.describe(
            waitTime="Die Abstimmungszeit in Minuten",
            content="Ihr Anliegen, welches abgestimmt werden soll",
            option1="Die erste Option",
            option2="Die zweite Option", 
            option3="Weitere Option falls benötigt",
            option4="Weitere Option falls benötigt",
            option5="Weitere Option falls benötigt"
        )
        async def abstimmung(interaction: discord.Interaction, waitTime : int, content : str, option1 : str, option2 : str, option3 : typing.Optional[str], option4: typing.Optional[str], option5: typing.Optional[str]):
            

            if waitTime >= self.maxWaitTime:
                if not await util.flugPermissionsHelper.canDoWrapper(DEFAULT_FLUGVOGEL_VOTER_CFG_PERMISSIONS_LONG_VOTE, interaction.user, None,
                self.permissions, self.logChannel):
                    await interaction.response.send_message(f"Bitte wählen Sie eine Abstimmungszeit, die kleiner als {self.maxWaitTime} Minuten ist.", ephemeral=True)
                 
                    return

            voteAmount = self.voteCount.get(str(interaction.user.id), 0)

            if voteAmount >= self.maxVotes:
                if not await util.flugPermissionsHelper.canDoWrapper(DEFAULT_FLUGVOGEL_VOTER_CFG_PERMISSIONS_MORE_VOTES,
                interaction.user, None, self.permissions, self.logChannel):
                    await interaction.response.send_message(f"Sie können maximal {self.maxVotes} Abstimmungen gleichzeitig eröffnen! Es laufen bereits {voteAmount} auf Ihrem Namen. Dieser Vorfall wird gemeldet🚔!", ephemeral=True)
                 
                    return
        
            if waitTime <= 0:
                await interaction.response.send_message("Bitte geben Sie eine größere Zahl als 0 als Abstimmungszeit ein.", ephemeral=True)
                await util.logHelper.logToChannelAndLog(self.logChannel, logging.WARNING, "🚧 Invalid Vote Request 🚧",
                f"{interaction.user.mention} passed invalid wait time: {waitTime}")              
  
                return

            options = []
            options.append(option1)
            options.append(option2)
            if option3:
                options.append(option3)
            if option4:
                options.append(option4)
            if option5:
                options.append(option5)

            #check if lengths are valid
            for opt in options:
                if not util.flugTextLength.isLabelLengthValid(opt):
                    await util.logHelper.logToChannelAndLog(self.logChannel, logging.WARNING, "🚧 Invalid Vote Request 🚧",
                    f"{self.moduleName} could not start Vote because invalid option with length {len(opt)} was passed by {interaction.user.mention}.")      

                    await interaction.response.send_message(f"Bitte geben Sie weniger als {util.flugTextLength.DEFAULT_DISCORD_MAX_LABEL_LENGTH} Zeichen bei den Optionen ein. Dieser Vorfall wird gemeldet🚔!", ephemeral=True)
                    return
        

            #increment users vote count
            self.voteCount.update({str(interaction.user.id):voteAmount+1})

            #embed for interaction response
            embed = discord.Embed(color=discord.Color.dark_grey())
            embed.set_author(name=interaction.user.name)
            embed.title = f"Abstimmung von {interaction.user.name}"

            #write end of vote on embed
            now = datetime.datetime.now()
            end = now + datetime.timedelta(minutes=waitTime)
            endString = end.strftime("%d/%m/%Y %H:%M:%S")
            embed.description = f"{interaction.user.mention} hat eine Abstimmung gestartet:\n **{content}**\n Die Abstimmung endet: {endString}"
        

            if not util.flugTextLength.isMessageLengthValid(embed.description):
                logging.critical(f"{self.moduleName} could not build embed.")
                return 

            #view for the response - One button for each option
            view = util.flugVoterHelper.VoteView(interaction, options)

            await interaction.response.send_message(embed=embed, view=view)
            originalResponse : discord.Message = await (await interaction.original_response()).fetch() #fetch original response
            await view.setReference(originalResponse)

            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "Vote started",
             f"{interaction.user.mention} started a vote in {interaction.channel.mention}")


            #wait
            await asyncio.sleep(60*waitTime)   

            #end vote
            embed.color = discord.Color.blurple()
            await view.endVote()
            await originalResponse.edit(embed=embed, view=view)
            

            #user vote count is back to prior value
            self.voteCount.update({str(interaction.user.id):voteAmount})

            await util.logHelper.logToChannelAndLog(self.logChannel, logging.INFO, "Vote ended",
             f"Vote from {interaction.user.mention} ended in {interaction.channel.mention}")            

        return True

CLASS = FlugVoter
