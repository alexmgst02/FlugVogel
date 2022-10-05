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
This section is currently missing. Help finding it! Config File template:
```json
{
    "guildID": 12345,
    "logConfig": {
        "logFile": "log.log",
        "logFileSize": 10000000.0,
        "logFileNum": 5,
        "logFormat": "[@ %(asctime)s]--[%(levelname)8s]--[%(filename)20s:%(funcName)20s()] %(message)s",
        "logLevel": "INFO"
    },
    "channels": "config/channels.json",
    "users": "config/users.json",
    "roles": "config/roles.json",
    "modules": "config/modules.json"
}
```

## Adding Modules
1. Come up with a module name; let's pick `FooModule`
2. Create `src/modules/FooModule.py` using this template:
    ```py
    import logging

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
    ```
    You can add your code after the greet-message (which you can also remove). You shouldn't change the signature of the `init`-function. The main task of that function should be registering callbacks using the `client`. `channels`, `users` and `roles` provide access to general information that may be needed to process events.
3. Add an entry for your module in `config/modules.json`. Assuming this is the only module, the file should look like this:
    ```json
    [
        {
            "name": "FooModule",
            "config": "FooModule.json"
        }
    ]
    ```
    _**Note**: The value of `config` will later be the `configFile` parameter of the `init`-Function for your module_.

## Deployment
Currently, only one method is documented:
```
$ ./start.sh <config_file_path> <token_file_path>
```