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
			"description": "no data other than your discord id and your config options will be stored by /reg/nal\nyou will not show up on message or talking stick leaderboards\nfor the most part, all this does is stop counting the messages you send",
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
		"general":
		{
			"hide_commands":
			{
				"description": "ignore user config and force all user commands to be hidden",
				"default": "disabled",
				"type": "ewbd"
			},
			"embed_color":
			{
				"description": "the color of all embeds\nformat: #69ff69 or ff69ff",
				"default": "69FF69",
				"type": "modal",
				"max_length": 7
			},
			"max_roll":
			{
				"description": "the max number you can roll with /roll\nnumber of both dice and sides\nmax is 16384",
				"default": 8192,
				"type": "modal",
				"max_length": 5
			},
		},
		"logging":
		{
			"enabled":
			{
				"description": "enable or disable logging",
				"default": False,
				"type": "bool"
			},
			"channel":
			{
				"description": "channel where logged messages will be sent",
				"default": None,
				"type": "channel"
			},
			"log_all_messages":
			{
				"description": "all sent messages, not just deleted and edited messages",
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
				"default": False,
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
		"qotd":
		{
			"enabled":
			{
				"description": "enable or disable question of the day\n\nonce per day at <t:1669568400:t> your time, a random question will be asked in the selected channel.",
				"default": False,
				"type": "bool"
			},
			"channel":
			{
				"description": "channel where questions will be asked",
				"default": None,
				"type": "channel"
			},
			"spawn_threads":
			{
				"description": "whether or not questions will be created with a thread",
				"default": False,
				"type": "bool"
			},
			"delete_after":
			{
				"description": "*no effect unless spawn_threads is enabled\ndelete threads when the next question is posted",
				"default": False,
				"type": "bool"
			},
		},
		"talking_stick":
		{
			"enabled":
			{
				"description": "enable or disable the talking stick\n\nonce per day at <t:1669568400:t> your time, a random active user will get the selected role.\nthis is typically used to allow the user to talk in a specific channel, but you could use it for anything.",
				"default": False,
				"type": "bool"
			},
			"channel":
			{
				"description": "channel to announce who has the talking stick",
				"default": None,
				"type": "channel"
			},
			"role":
			{
				"description": "role to be given out",
				"default": None,
				"type": "role"
			},
			"limit":
			{
				"description": "seperate role required to be eligible for the talking stick",
				"default": None,
				"type": "role"
			}
		},
		"auto_responses":
		{
			"enabled":
			{
				"description": "automatic responses to certain words or phrases",
				"default": "enabled",
				"type": "ewbd"
			},
			"cooldown":
			{
				"description": "time (in seconds) after sending an auto response where another one will not be sent",
				"default": 0,
				"type": "modal",
				"max_length":3
			}
		},
		"dad_bot":
		{
			"enabled":
			{
				"description": "it's just dad bot",
				"default": "disabled",
				"type": "ewbd"
			},
			"cooldown":
			{
				"description": "time (in seconds) after sending a dad bot message where another one will not be sent",
				"default": 0,
				"type": "modal",
				"max_length":3
			}
		}
	},
	"dev":
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