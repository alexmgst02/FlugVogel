# FlugVogel-Beta
This is the early beta version of the **FlugVogel** Discord Bot used to manage the community Discord Server of the Fakultät IV @ TU Berlin! It's written in Python3 using [`discord.py`](https://pypi.org/project/discord.py/).

This project tries to be as modular as possible! Documentation on how to use modules and write new ones will be added soon!

## Quickstart
To start using the bot, you'll have to:
1. Create the bot on the [Discord Developer Portal](https://discordapp.com/developers/applications/). Note down the Token generated for your bot.
2. Install the required Python Dependencies.
```
$ pip install --user -r requirements.txt
```
3. Setup your authentication token file, see [Authentication Token](#authentication-token).
4. Configure **FlugVogel** to suit your needs, see [Configuration](#configuration).
5. Deploy your **FlugVogel** instance! See [Deployment](#deployment).

## Authentication Token
To function, **FlugVogel** need its authentication token! You should put it into a `json` file with the following structure:
```json
{
    "token": "TOKEN"
}
```
... while `TOKEN` needs to be replaced with the actual token. How about naming it `token.json`? This way it will be `git-ignored` by default!

## Configuration
This section is currently missing. Help finding it!

## Deployment
Currently, only one method is documented:
```
$ ./start.sh <config_file_path> <token_file_path>
```