import discord
from discord.utils import get
import asyncio
import re
import aiomysql
import flugvogeldata
import random
import datetime
from discord.ext import tasks
#intents
intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
#wichtige variablen
roles = flugvogeldata.roles
msg1 = flugvogeldata.metafrage
role_channel_id = flugvogeldata.channel_ids["roles"]
admin = flugvogeldata.role_ids["admin"]
mod = flugvogeldata.role_ids["mod"]
ban_role_id = flugvogeldata.role_ids["ban"]
welcome_channel_id = flugvogeldata.channel_ids["welcome"]
log_channel_id = flugvogeldata.channel_ids["log"]
statistic_channel_id = flugvogeldata.channel_ids["statistiken"]
async def log(author=False, channel=False, command=""): #user, channel, string
    log_channel = client.get_channel(log_channel_id)
    if author and channel:
        await log_channel.send(f"{author.mention} hat ** [command] ** {command} ** in [channel] **{channel.mention} genutzt.") 
    else:
        await log_channel.send(command)

async def in_database(loop, id): #Überprüft, ob ein member bereits in der datenbank steht
    conn = await aiomysql.connect(host='localhost', user='admin', password="raspberry", db="discord", loop=loop)

    cur = await conn.cursor()
    async with conn.cursor() as cur:
        await cur.execute("SELECT COUNT(ID) FROM users WHERE ID = %s;", int(id))
        count = await cur.fetchall() #count unformatted
        count = int(re.sub(r'[^\w]', '', str(count))) #count format
        if count > 0:
            await cur.close()
            conn.close()
            return True
        else:
            await cur.close()
            conn.close()
            return False


async def insert_database(loop, id): #datenbanken einträge für ausschluss
    conn = await aiomysql.connect(host='localhost', user='admin', password="raspberry", db="discord", loop=loop)
    cur = await conn.cursor()
    async with conn.cursor() as cur:
        await cur.execute("INSERT INTO users (ID) VALUES (%s);", int(id))
        await conn.commit()
        await cur.close()
        conn.close()
        print(str(id) + " erfolgreich in die Datenbank inserted.")

async def ausschluss(guild, ban_user, channel): #entfernen von rollen und ausschluss aus server
    role = get(guild.roles, id=ban_role_id)
    ban_member = await guild.fetch_member(int(ban_user))
    print(ban_member)
    for r in ban_member.roles:
        if r.name == "Admin":
            return
        try:
            await ban_member.remove_roles(r)
        except:
            pass
    await ban_member.add_roles(role)
    loop = asyncio.get_event_loop()
    if await in_database(loop, ban_user) == True:
        await channel.send(str(ban_member.name) + " wurde bereits ausgeschlossen.")
        return
    loop = asyncio.get_event_loop()
    await insert_database(loop, ban_user)
    await channel.send(ban_member.name + " wurde von diesem Server gebannt. <:laserpo:936010625648316416>")

async def unban(loop, id):

    if await in_database(loop, id):
        conn = await aiomysql.connect(host='localhost', user='admin', password="raspberry", db="discord", loop=loop)
        cur = await conn.cursor()
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM users WHERE ID=%s;", int(id))
            await conn.commit()
            await cur.close()
            conn.close()
            print(str(id) + " erfolgreich aus der datenbank entfernt.")

@client.event
async def on_member_join(member):
    welcome_channel = client.get_channel(welcome_channel_id)
    loop = asyncio.get_event_loop()
    if await in_database(loop, member.id): #wenn der member gebannt wurde -> erneut ausschluss
        await ausschluss(member.guild , member.id, welcome_channel)

@client.event
async def on_ready():
    print('Ich bin als {0.user} eingeloggt'.format(client))
    game = discord.Game("!altklausuren")
    await client.change_presence(status=discord.Status.online, activity=game)
    if not statistic_updates.is_running():
        statistic_updates.start()


@client.event
async def on_message(message):
    if message.content.lower().startswith("!vote"): #vote funktionalität
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        await log(message.author, message.channel, "!vote")

    if message.content.lower().startswith("!metafrage"): #metafrage
        await message.channel.send(msg1)
        await message.delete()
        await log(message.author, message.channel, "!metafrage")

    if message.channel.id == role_channel_id and message.author != client.user: #role handling
        try:
            role = get(message.guild.roles, name=message.content)
            if role.name in roles:
                await message.author.add_roles(role)
                await log(command=f"{message.author.mention} hat sich die Rolle **{role}** gegeben")
        except Exception as e:
            await message.channel.send(message.author.name + ", das hat nicht geklappt. Bitte so schreiben wie oben angegeben.")
            await log(command=f"{message.author.mention} hat versucht sich die Rolle '{message.content}' zu geben")
            print(e)
        await message.delete()

    if message.content.lower().startswith("!ausschluss") or message.content.lower().startswith("!unban"): #start von !ausschluss. evtl. instabil bei re.sub
        for cmd_role in message.author.roles:
            if cmd_role.id == admin or cmd_role.id == mod:
                try:
                    parts = message.content.split(" ")
                    ban_id = parts[1]
                    ban_id = re.sub(r'[^\w]', '', ban_id)
                    ban_id = ban_id[:18]
                    if message.content.lower().startswith("!ausschluss"):
                        await ausschluss(message.guild, ban_id, message.channel)
                        await log(message.author, message.channel, message.content)
                    else:
                        loop = asyncio.get_event_loop()
                        await unban(loop, ban_id)
                        ban_member = await message.guild.fetch_member(int(ban_id))
                        for r in ban_member.roles:
                            try:
                                await ban_member.remove_roles(r)
                            except:
                                pass
                        await log(message.author, message.channel, message.content)
                except Exception as e:
                    await log(command="error bei !ausschluss: " + str(e))
                    await message.channel.send(message.author.name + ", das hat nicht geklappt.")
        await message.delete()

    if message.content.lower().startswith("!fristen"):
        link = flugvogeldata.fristen
        await message.channel.send(link)
        await log(message.author, message.channel, "!fristen")
        await message.delete()

    if message.content.lower().startswith("!altklausuren"): #altklausuren
        link = flugvogeldata.get__klausur_link(message.channel.id)
        await message.channel.send(link)
        await log(message.author, message.channel, "!altklausuren")
        await message.delete()




async def get_top_elements(length, dic):
    top_elements_count =[]
    top_elements = []
    top_elements_count = [0 for i in range(length)]
    top_elements = [0 for i in range(length)]
    for key, value in dic.items():
        i = 0
        while i < length and value > top_elements_count[i]:
            if i < length-1 and value > top_elements_count[i+1]:
                top_elements_count[i] = top_elements_count[i+1]
                top_elements[i] = top_elements[i+1]
            else:
                if i > 0:
                    top_elements[i-1] = top_elements[i]
                    top_elements_count[i-1] = top_elements_count[i]
                if value > top_elements_count[i]:    
                    top_elements[i] = key
                    top_elements_count[i] = value
                break
            i += 1
        if value > top_elements_count[i]:    
            top_elements_count[i] = value
            top_elements[i] = key
    return top_elements

@tasks.loop(minutes = 10080)
async def statistic_updates():
    today = datetime.datetime.now()
    week_ago = today - datetime.timedelta(days=7)
    guild = client.get_guild(1026808694773649449)
    emote_count = {}
    channel_count = {}
    word_count = {}
    all_emote_names = []
    top_chatters = {}
    all_words = 0
    all_messages = 0
    for c in guild.text_channels:
        if c.name == "team" or c.name == "log" or c.name == "regeln" or c.name == "is-isis-down" or c.name == "statistiken":
            continue
        async for msg in c.history(limit=None, after=week_ago):
            all_messages += 1
            if c not in channel_count:
                channel_count.update({c: 0})
            channel_count.update({c: channel_count[c] + 1})
            custom_emojis = re.findall(r'<:\w*:\d*>', msg.content)
            for em in custom_emojis:
                if em not in all_emote_names:
                    all_emote_names.append(em)
                e = int(em.split(':')[2].replace('>', ''))
                e = discord.utils.get(client.emojis, id=e)
                if e not in emote_count and e is not None:
                    emote_count.update({e: 1})
                    continue
                if e is not None:
                    emote_count.update({e: emote_count[e] + 1})
            for word in msg.content.lower().split():
                if word not in all_emote_names and word is not None:
                    all_words += 1
                    if word not in word_count:
                        word_count.update({word: 1})
                        continue
                    word_count.update({word: word_count[word] + 1})
            if msg.author not in top_chatters:
                top_chatters.update({msg.author:1})
                continue
            top_chatters.update({msg.author: top_chatters[msg.author]+1})
    
    top_emotes = await get_top_elements(3, emote_count)
    top_channels = await get_top_elements(3, channel_count)
    top_chatters2 = await get_top_elements(5, top_chatters)
    statistics_update = ("Hier die aktuellen Statistiken der letzten Woche:\n\nDie beliebtesten Kanäle:\nPlatz 1: " +
                         top_channels[2].mention + " mit " + str(channel_count[top_channels[2]]) + " Nachrichten\n" +
                         "Platz 2: " + top_channels[1].mention + " mit " + str(
                channel_count[top_channels[1]]) + " Nachrichten\n" +
                         "Platz 3: " + top_channels[0].mention + " mit " + str(
                channel_count[top_channels[0]]) + " Nachrichten\n\n" +
                         "Hier folgen die beliebtesten Emotes:\n" +
                         "Platz 1: " + str(top_emotes[2]) + " mit " + str(
                emote_count[top_emotes[2]]) + " Verwendungen\n" +
                         "Platz 2: " + str(top_emotes[1]) + " mit " + str(
                emote_count[top_emotes[1]]) + " Verwendungen\n" +
                         "Platz 3: " + str(top_emotes[0]) + " mit " + str(emote_count[top_emotes[0]]) + " Verwendungen"
                         )
    fact_decider = random.randint(1, 2)
    fun_fact = "Mehr oder weniger interessante Zusatzinformation: "
    if fact_decider == 1:
        unused_emotes = []
        for emoji in guild.emojis:
            if emoji not in emote_count:
                unused_emotes.append(emoji)
        fun_fact += "der emote " + str(random.choice(
            unused_emotes)) + " wurde die letze Woche 0 Mal verwendet."

    elif fact_decider == 2:
        interval = -random.randint(round(len(word_count) / 50), round(len(word_count) / 10))
        most_popular_word = sorted(word_count.items(), key=lambda x: x[1])[interval]
        fun_fact += "Das Wort '" + str(most_popular_word[0]) + "' wurde " + str(most_popular_word[1]) + " mal verwendet"
    top_messages = top_chatters[top_chatters2[0]] + top_chatters[top_chatters2[1]] + top_chatters[top_chatters2[2]]  + top_chatters[top_chatters2[3]] + top_chatters[top_chatters2[4]]

    dataset = {}
    dataset.update(emote_count)
    dataset.update(channel_count)
    dataset.update(top_chatters)
    dataset.update(word_count)
    ratio = str(top_messages/all_messages *100)+"%"
    await client.get_channel(statistic_channel_id).send(statistics_update + "\n\n")
    await log(command=f"Die wöchentlichen Statistiken sind da. Die aktivsten chatter:\n{top_chatters2[0].mention}\n{top_chatters2[1].mention}\n{top_chatters2[2].mention}\n{top_chatters2[3].mention}\n{top_chatters2[4].mention}\nSie schrieben {ratio} der nachrichten\n\n" + fun_fact + "\nHier das ganze Datenset: ")
    with open("dataset.txt", "w") as data_file:
        for key, value in emote_count.items():
            data_file.write(f"{key} : {value}\n")
    log_channel = client.get_channel(log_channel_id)
    with open("dataset.txt" , "rb") as data_file:
        await log_channel.send("Dataset1: ", file=discord.File(data_file, "emote_usage.txt"))
    
    with open("dataset.txt", "w") as data_file:
        for key, value in channel_count.items():
            data_file.write(f"{key} : {value}\n")
    with open("dataset.txt" , "rb") as data_file:
        await log_channel.send("Dataset2: ", file=discord.File(data_file, "channel_usage.txt"))

    with open("dataset.txt", "w",encoding="utf-8") as data_file:
        for key, value in top_chatters.items():
            data_file.write(f"{key} : {value}\n")
    with open("dataset.txt" , "rb") as data_file:
        await log_channel.send("Dataset3: ", file=discord.File(data_file, "chatters.txt"))
client.run("MTAyNjgxMTM5NDQ1ODM5MDU3MA.G9fJ62.rDxzqHjSArgPBEqpDX1bPGLa4bLMCearnXXO9s")
