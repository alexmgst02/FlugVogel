import discord
import logging
import datetime

async def logToChannelAndLog(channel: discord.TextChannel, logLevel: int, embedTitle: str, logMessage: str):
    # create an embed
    embed = discord.Embed(title=embedTitle, description=logMessage)

    # check the level for the embed colour
    if logLevel == logging.CRITICAL or logLevel == logging.ERROR:
        embed.colour = discord.Colour.red()
    elif logLevel == logging.WARNING:
        embed.colour = discord.Colour.yellow()
    elif logLevel == logging.INFO:
        embed.colour = discord.Colour.blue()
    else:
        embed.colour = discord.Colour.og_blurple()

    # set the timestamp
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

    # send to the channel
    await channel.send(embed=embed)
    
    # log it
    logging.log(logLevel, logMessage)
