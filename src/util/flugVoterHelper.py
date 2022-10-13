from typing import List
import discord


DEFAULT_FLUGVOGEL_VOTER_HELPER_MODES = [0,1,2,3,4,5]
DEFAULT_DISCORD_MAX_LABEL_LENGTH = 80

#This button receives a label and custom_id on init. If pressed it increments a voting
#counter. The View should be of type VoteView.
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
        if len(self.labelText + f" ({self.count})") > DEFAULT_DISCORD_MAX_LABEL_LENGTH:
            return

        self.label = self.labelText + f" ({self.count})"

    def decrementCount(self):
        key = self.view.translateToOpt.get(int(self.custom_id))
        currentVotes = self.view.voteResults.get(key, 1)
        self.count -= 1
        self.view.voteResults.update({key:currentVotes-1})
        self.refreshLabel()        

    def incrementCount(self):
        key = self.view.translateToOpt.get(int(self.custom_id))
        currentVotes = self.view.voteResults.get(key, 0)
        self.count += 1
        self.view.voteResults.update({key:currentVotes+1})
        self.refreshLabel()        



    async def callback(self, interaction: discord.Interaction):
        self.view : VoteView
        userStatus = self.view.votes.get(str(interaction.user.id))


        #has not voted before
        if userStatus == None:
            self.view.votes.update({str(interaction.user.id):self.mode})
            self.incrementCount()
            
        #wants to change vote
        elif userStatus != self.mode:
            self.view.votes.update({str(interaction.user.id):self.mode})
            self.incrementCount()
            #remove prior vote
            for btn in self.view.children:
                if btn.custom_id == str(userStatus):
                    btn.decrementCount()
                    break
            
        #wants to remove vote
        else:
            self.view.votes.update({str(interaction.user.id):None})
            self.decrementCount()

        await interaction.response.edit_message(view=self.view)


class VoteView(discord.ui.View):
    votes : dict = None
    children : List[VoteButton]
    voteInteraction : discord.Interaction = None
    voteResults : dict = None
    translateToOpt : dict = None    #custom_id : label

    #Pass the options which can be voted for as options and the 
    #original Interaction as interaction.
    def __init__(self, interaction : discord.Interaction, options : List[str]):
        super().__init__(timeout=None)

        self.voteInteraction = interaction

        self.votes = {}
        self.voteResults = {}
        self.translateToOpt = {}

        for i in range(len(options)):
            tmpButton = VoteButton(options[i], DEFAULT_FLUGVOGEL_VOTER_HELPER_MODES[i])
            self.add_item(tmpButton)
            self.translateToOpt.update({DEFAULT_FLUGVOGEL_VOTER_HELPER_MODES[i]:options[i]})
            self.voteResults.update({options[i]:0})

    async def endVote(self):
        self.voteResults = dict(sorted(self.voteResults.items(), key=lambda item: item[1]))    

        embed = discord.Embed(color=discord.Color.brand_green())
        embed.set_author(name=self.voteInteraction.user.name, icon_url=self.voteInteraction.user.display_avatar)
        embed.title = f"Abstimmung von {self.voteInteraction.user.name}"

        result = f"Die Abstimmung ist vollendet! Es haben\n"
        for key,value in self.voteResults.items():
            result += f"{value} Nutzer für '{key}'\n"

        result += "abgestimmt."
        embed.description = result
        
        self.clear_items()
        self.stop()

        response = await self.voteInteraction.original_response()
        await self.voteInteraction.channel.send(embed=embed, reference=response.to_reference())        
