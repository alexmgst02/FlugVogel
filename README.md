# FlugVogel-Bot
This is the **FlugVogel** Discord Bot used to manage the community Discord Server of the Fakultät IV @ TU Berlin! It's written in Python3 using [`discord.py`](https://pypi.org/project/discord.py/).

Opposite to many Discord Bots, you'll need to host this one yourself if you intend to use it. It follows a modular design pattern. This repository contains modules that we felt were useful and necessary for its purpose.

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
Configuring **FlugVogel** can be split into two parts, configuring the core functionality of the bot and configuring its modules. It usually is a good idea to put all config files into a folder called `config`. The main config file may be located in `config/config.json`, and has contents according to the following "template":
```json
{
    "guildID": 12345,               /* ID of the Guild the FlugVogel shall operate on */
    "logConfig": {
        "logFile": "log.log",       /* Where FlugVogel shall log to besides /dev/stdout */
        "logFileSize": 10000000.0,  /* The maximum amount of byets a log file can grow to */
        "logFileNum": 5,            /* The amount of old log files to keep */
        "logFormat": "[@ %(asctime)s]--[%(levelname)8s]--[%(filename)20s:%(funcName)20s()] %(message)s", /* The log format */
        "logLevel": "INFO"          /* The log level */
    },
    "channels": "config/channels.json", /* Where the Channels-Config is located at */
    "users": "config/users.json",       /* Where the Users-Config is located at */
    "roles": "config/roles.json",       /* Where the Roles-Config is located at */
    "modules": "config/modules.json",   /* Where the Modules-Config is located at */
}
```
For information on the `logFormat` and `logLevel`, see [Python Logging](https://docs.python.org/3/howto/logging.html). All sub-config paths contained in the main config are relative to the directory **FlugVogel** will be executed from, which should be the root of the repository. Alternatively, absolute paths can be provided.

See the [Channel Config](#channelsjson), [User Config](#usersjson), [Role Config](#rolesjson) and [Module Config](#modulesjson).

### `channels.json`
The Channel-Config contains information about channels **FlugVogel** or any of its modules need to operate on. This should be the only config file which contains channel IDs. Modules may introduce new fields to this config is necessary as long as the general format isn't broken. Modules are allowed to create new channel entries.
```json
{
    "12345": {                  /* Example Channel ID */
        "name": "example_name", /* Internal name of the Channel*/
        /*
         * Optional, if set to true, this option will tell the FlugRoleAssigner
         * module that this channel is used for users picking their roles.
         */
        "isRoleAssignmentChannel": false,
        /*
         * Optional, if set to true, this option will tell FlugStatistics to NOT
         * scan messages in this channel when generating statistics.
         */
        "statsIgnore": true,
    }
}
```
**Note** that the name doesn't have to match the actual name of the channel. It should only be used by other parts of **FlugVogel**, such as modules, to search for this channel. Module specific configurations should then only contain the name under which the channel is configured in this file.

### `users.json`
The User-Config contains information about specific users. The main usecase of this module is storing information about muted/banned users, ... It should be the only file containing user IDs. Modules may introduce new fields to this config is necessary as long as the general format isn't broken. Modules are allowed to create new user entries.
```json
{
    "12345": {
        "banned": false /* Will be set by the FlugUserDeactivator */
    }
}
```

### `roles.json`
The Role-Config contains information about specific roles. It should be the only file containing role IDs. Modules may introduce new fields to this config is necessary as long as the general format isn't broken. Modules are allowed to create new user entries.
```json
{
    "12345": {
        "name": "example_name", /* Internal name of the role */
        /*
         * Needed for the "FlugRoleAssigner" module. Sets whether users can assign
         * this role to themselves using the assigner (true) or not (false).
         */
        "assignable": false
    }
}
```

### `modules.json`
The Module-Config tells **FlugVogel** which modules to load.
```json
[
    {
        "name": "FlugFoo",               /* Name of the module */
        "config": "config/FlugFoo.json", /* Config file for the module */
        "optional": true,                /* Whether the module is optional */
        "enabled": false                 /* Whether the module is enabled */
    },
    {
        /* ... */
    }
]
```
The `name` **must** match the name of the Python file in `src/modules/`, excluding the `.py` extension. The matching is case sensitive. The `config` path will be passed to the module.
If the module doesn't need a config, the value of this doesn't matter. If `optional` is set to `true`, the module failing to initialize will mearly cause a warning log message, but the bot will still continue to run. If set to `false`, the bot would refuse to start in such a case. `enabled` controls whether the module shall be loaded and initialized.

## Adding Modules
1. Come up with a module name; let's pick `FooModule`
2. Create `src/modules/FooModule.py` using this template. It must implement the `FlugModule` class specified in `src/modules/FlugModule.py`.
3. Add an entry for your module in `config/modules.json`, see [Module Config](#modulesjson).
Note that the `config` attribute will be the `configFilePath` parameter in your code.
4. Adapt other config files, see [Configuration](#configuration), if any changes are necessary.

**Important**: You must **NOT** use the `@client.event` method provided by [`discord.py`](https://pypi.org/project/discord.py/) to register, for example, `on_message` functions, or any similar functions. Use the `addSubscriber` or `subscribeTo` methods provided by the `FlugClient` class instead. An instance of the `FlugClient` class is passed to each module.
```py
# ...
async def process_message(self, message: discord.Message):
    # ... do things ...

def setup(self):
    # ... do things ...
    self.client.addSubscriber('on_message', self.process_message)
```
The `subscribeTo` method can be used as an annotation, just like `@client.event` would usually be used.

## Deployment
Currently, only one method is documented, from the root of the repository:
```
$ python src/FlugVogel.py <config_file_path> <token_file_path>
```