config = {
    "user":
    {
      "ignored":
      {
        "description": "/reg/nal will ignore you.\ndadbot and auto responses will not respond to your messages.\nyou also cannot recieve the talking stick.",
        "default": False,
        "type": "bool"
      },
      "hide_commands":
      {
        "description": "hide your command usage\nall commands used will be sent as hidden messages\nif set to False, some private commands will still be hidden like /get_data",
        "default": True,
        "type": "bool"
      },
      "no_track":
      {
        "description": "no data other than your discord id and your config options will be stored by /reg/nal\nyou will not show up on message or talking stick leaderboards\nyou also will not have your birthday announced",
        "default": False,
        "type": "bool"
      },
      "talking_stick":
      {
        "description": "allows you to recieve the talking stick.\ndisable if you're getting unwanted pings.",
        "default": True,
        "type": "bool"
      }
    },
    "guild":
    {
      "auto_responses":
      {
        "description": "enable or disable auto responses\ndoes not disable dad bot",
        "default": "enabled",
        "type": "str"
      },
      "dad_bot":
      {
        "description": "enable or disable dad bot\ndoes not disable auto responses",
        "default": "disabled",
        "type": "str"
      },
      "hide_commands":
      {
        "description": "ignore user config and force all user commands to be hidden",
        "default": "disabled",
        "type": "str"
      },
      "talking_stick":
      {
        "description": "talking stick rolls",
        "default": False,
        "type": "bool"
      },
      "qotd":
      {
        "description": "question of the day",
        "default": False,
        "type": "bool"
      },
      "embed_color":
      {
        "description": "the color of the embeds\nformat: #69ff69 or ff69ff",
        "default": "#69FF69",
        "type": "input",
        "max_length": 7
      },
      "max_roll":
      {
        "description": "the max number you can roll with /roll\nnumber of both dice and sides\nmax is 16384",
        "default": 8192,
        "type": "input",
        "max_length": 5
      }
    },
    "logging":
    {
      "enabled":
      {
        "description": "enable or disable logging",
        "default": False,
        "type": "bool"
      },
      "log_all_messages":
      {
        "description": "set messages, not just deleted and edited messages",
        "default": False,
        "type": "bool"
      },
      "deleted_messages":
      {
        "description": "announce deleted messages to the logging channel",
        "default": True,
        "type": "bool"
      },
      "edited_messages":
      {
        "description": "announce edited messages to the logging channel",
        "default": True,
        "type": "bool"
      },
      "filtered_messages":
      {
        "description": "announce filtered messages to the logging channel",
        "default": True,
        "type": "bool"
      },
      "member_join":
      {
        "description": "announce member joins to the logging channel",
        "default": False,
        "type": "bool"
      },
      "member_leave":
      {
        "description": "announce member leaves to the logging channel",
        "default": False,
        "type": "bool"
      },
      "log_bots":
      {
        "description": "log bot messages",
        "default": False,
        "type": "bool"
      }
    },
    "/reg/nal":
    {
      "command_stdout":
      {
        "description": "log command usage to /reg/log",
        "default": True,
        "type": "bool"
      },
      "stick_stdout":
      {
        "description": "log talking stick rolls to /reg/log",
        "default": False,
        "type": "bool"
      },
      "listener_stdout":
      {
        "description": "log dadbot and auto responses usage to /reg/log",
        "default": False,
        "type": "bool"
      },
      "info_stdout":
      {
        "description": "log info to /reg/log",
        "default": True,
        "type": "bool"
      },
      "error_stdout":
      {
        "description": "log errors to /reg/log",
        "default": True,
        "type": "bool"
      },
      "debug_stdout":
      {
        "description": "log debug to /reg/log",
        "default": False,
        "type": "bool"
      },
      "extension_loading":
      {
        "description": "whether or not to load extensions",
        "default": True,
        "type": "bool"
      },
      "bypass_permissions":
      {
        "description": "whether or not the bot owner can bypass guild permissions",
        "default": True,
        "type": "bool"
      }
    }
  }