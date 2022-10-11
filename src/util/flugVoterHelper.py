from typing import List
import discord
import datetime


DEFAULT_FLUGVOGEL_VOTER_HELPER_MODES = [0,1,2,3,4,5]

class VoteButton(discord.ui.Button):
    mode : int = None
    count : int = None
    labelText : str = None

    def __init__(self, label : str, mode : int):
        super().__init__(label=label, style=discord.ButtonStyle.green, custom_id=str(mode))
        self.mode = mode
        self.count = 0
        self.labelText = label

    def refreshLabel(self):
        if self.count == 0:
            self.label = self.labelText
            return

        self.label = self.labelText + f" ({self.count})"


    async def callback(self, interaction: discord.Interaction):
        self.view : VoteView
        userStatus = self.view.votes.get(str(interaction.user.id))

        key = self.view.translateToOpt.get(int(self.custom_id))
        currentVotes = self.view.voteResults.get(key, 0)

        #has not voted before
        if userStatus == None:
            self.view.votes.update({str(interaction.user.id):self.mode})
            self.view.voteResults.update({key:currentVotes+1})
            self.count += 1
            self.refreshLabel()

        #wants to change vote
        elif userStatus != self.mode:
            self.view.votes.update({str(interaction.user.id):self.mode})
            keyDel = self.view.translateToOpt.get(int(userStatus))
            voteDel = self.view.voteResults.get(keyDel, 1)              
            self.view.voteResults.update({key:currentVotes+1})
            self.view.voteResults.update({keyDel:voteDel-1})
            #remove prior vote
            for btn in self.view.children:
                if btn.custom_id == str(userStatus):
                    btn.count -= 1
                    btn.refreshLabel()
                    break
            
            self.count += 1
            self.refreshLabel()
        
        #wants to remove vote
        else:
            self.view.voteResults.update({key:currentVotes-1})

            self.view.votes.update({str(interaction.user.id):None})
            self.count -= 1
            self.refreshLabel()

        await interaction.response.edit_message(view=self.view)

class VoteView(discord.ui.View):
    votes : dict = None
    agree : int = 0
    disagree : int = 0
    children : List[VoteButton]
    voteInteraction : discord.Interaction = None
    voteResults : dict = None
    translateToOpt : dict = None

    def __init__(self, timeout : int, interaction : discord.Interaction, options : List[str]):
        super().__init__(timeout=timeout)

        self.voteInteraction = interaction

        self.votes = {}
        self.voteResults = {}
        self.translateToOpt = {}

        for i in range(len(options)):
            tmpButton = VoteButton(options[i], DEFAULT_FLUGVOGEL_VOTER_HELPER_MODES[i])
            self.add_item(tmpButton)
            self.translateToOpt.update({DEFAULT_FLUGVOGEL_VOTER_HELPER_MODES[i]:options[i]})

    async def on_timeout(self):
        

        print(self.voteResults)
            


        embed = discord.Embed(color=discord.Color.brand_green())
        embed.set_author(name=self.voteInteraction.user.name, icon_url=self.voteInteraction.user.display_avatar)
        embed.title = f"Abstimmung von {self.voteInteraction.user.name}"

        result = f"Die Abstimmung ist vollendet! "

        if agree == 1:
            result += f"1 Nutzer stimmte für Ja, "
        else:
            result += f"{agree} Nutzer stimmten für Ja, "

        if disagree == 1:
            result += "1 Nutzer stimmte für Nein\n"
        else:
            result += f"{disagree} Nutzer stimmten für Nein\n"

        if agree > disagree:
            result += "Somit hat die Mehrheit für Ja gestimmt✅"
        elif disagree > agree:
            result += "Somit ist das Ergebnis Nein❌"
        else:
            result += "Gleichstand! ❎"

        embed.description = result

        response = await self.voteInteraction.original_response()
        await self.voteInteraction.channel.send(embed=embed, reference=response.to_reference())        


class VoteManager():
    view : VoteView = None
    embed : discord.Embed = None
    voteInteraction : discord.Interaction = None
    waitTime : int = None
    embedContent : str = None
    voteOptions : List[str] = None
    def __init__(self, waitTime : int, interaction : discord.Interaction, content : str, options : List[str]):

        self.embed = discord.Embed(color=discord.Color.dark_grey())
        self.voteInteraction = interaction
        self.waitTime = waitTime
        self.embedContent = content
        self.voteOptions = options

    def buildEmbed(self) -> bool:
        self.embed.set_author(name=self.voteInteraction.user.name)
        self.embed.title = f"Abstimmung von {self.voteInteraction.user.name}"

        now = datetime.datetime.now()
        end = now + datetime.timedelta(minutes=self.waitTime)
        endString = end.strftime("%d/%m/%Y %H:%M:%S")
        self.embed.description = f"{self.voteInteraction.user.mention} hat eine Abstimmung gestartet:\n **{self.embedContent}**\n Die Abstimmung endet: {endString}"
        

        if len(self.embed.description) > 2000:
            return False

        return True

    async def startVote(self):
        self.view = VoteView(self.waitTime*60, self.voteInteraction, self.voteOptions)

        await self.voteInteraction.response.send_message(embed=self.embed, view=self.view)   


        