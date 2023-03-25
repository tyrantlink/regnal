from pymongo.collection import Collection
from .mongo_object import MongoObject

class INF(MongoObject):
	def __init__(self,db,col:Collection,_id) -> None:
		super().__init__(db,col,_id,[])
		"""Collection\n\nraw mongodb collection"""
		self._id = MongoObject(db,col,_id,['_id'])
		"""str\n\ndocument id, should only be '/reg/nal'"""
		self.version = MongoObject(db,col,_id,['version'])
		"""str\n\nbot version"""
		self.command_usage = MongoObject(db,col,_id,['command_usage'])
		"""dict[str,int]\n\ncommand usage"""
		self.env = MongoObject(db,col,_id,['env'])
		"""dict[str,str]\n\nenvironment variables"""
		self.extensions = MongoObject(db,col,_id,['extensions'])
		"""dict[str,bool]\n\nenable / disable extensions"""
		self.transcription = MongoObject(db,col,_id,['transcription'])
		"""dict[str,str]\n\ntts transcription"""
		self.auto_responses = MongoObject(db,col,_id,['auto_responses'])
		"""dict[str,dict]\n\nauto responses"""
		self.banned_users = MongoObject(db,col,_id,['banned_users'])
		"""list[int]\n\nlist of banned user ids"""
		self.config = self.___config(db,col,_id,['config'])
		"""dict[str,bool|int|list]\n\ndev config options"""

	class ___config(MongoObject):
		def __init__(self,db,col,_id,path) -> None:
			super().__init__(db,col,_id,path)
			self.bypass_permissions = MongoObject(db,col,_id,['config','bypass_permissions'])
			"""bool"""
			self.guild = MongoObject(db,col,_id,['config','guild'])
			"""int"""
			self.change_log = MongoObject(db,col,_id,['config','change_log'])
			"""int"""
			self.support = MongoObject(db,col,_id,['config','support'])
			"""int"""
			self.error_wh = MongoObject(db,col,_id,['config','error_wh'])
			"""str"""
			self.support_wh = MongoObject(db,col,_id,['config','support_wh'])
			"""str"""
			self.donation_roles = MongoObject(db,col,_id,['config','donation_roles'])
			"""list[int]"""

class Guild(MongoObject):
	def __init__(self,db,col:Collection,_id) -> None:
		super().__init__(db,col,_id,[])
		"""Collection\n\nraw mongodb collection"""
		self._id = MongoObject(db,col,_id,['_id'])
		"""int|str\n\ndiscord guild id"""
		self.name = MongoObject(db,col,_id,['name'])
		"""str\n\ndiscord server name"""
		self.owner = MongoObject(db,col,_id,['owner'])
		"""str\n\ndiscord owner id"""
		self.config = self.___config(db,col,_id,['config'])
		"""dict[str,dict]\n\nguild configuration options"""
		self.data = self.___data(db,col,_id,['data'])
		"""dict[str,dict]\n\nguild data storage"""

	class ___config(MongoObject):
		def __init__(self,db,col,_id,path) -> None:
			super().__init__(db,col,_id,path)
			self.general = self.___general(db,col,_id,['config','general'])
			"""dict[str,dict]"""
			self.logging = self.___logging(db,col,_id,['config','logging'])
			"""dict[str,dict]"""
			self.tts = self.___tts(db,col,_id,['config','tts'])
			"""dict[str,dict]"""
			self.qotd = self.___qotd(db,col,_id,['config','qotd'])
			"""dict[str,dict]"""
			self.talking_stick = self.___talking_stick(db,col,_id,['config','talking_stick'])
			"""dict[str,dict]"""
			self.auto_responses = self.___auto_responses(db,col,_id,['config','auto_responses'])
			"""dict[str,dict]"""
			self.dad_bot = self.___dad_bot(db,col,_id,['config','dad_bot'])
			"""dict[str,dict]"""

		class ___general(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.hide_commands = MongoObject(db,col,_id,['config','general','hide_commands'])
				"""str"""
				self.embed_color = MongoObject(db,col,_id,['config','general','embed_color'])
				"""str"""
				self.max_roll = MongoObject(db,col,_id,['config','general','max_roll'])
				"""int"""
				self.pluralkit = MongoObject(db,col,_id,['config','general','pluralkit'])
				"""bool"""
				self.moderator_role = MongoObject(db,col,_id,['config','general','moderator_role'])
				"""int"""

		class ___logging(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.enabled = MongoObject(db,col,_id,['config','logging','enabled'])
				"""bool"""
				self.channel = MongoObject(db,col,_id,['config','logging','channel'])
				"""int"""
				self.log_all_messages = MongoObject(db,col,_id,['config','logging','log_all_messages'])
				"""bool"""
				self.deleted_messages = MongoObject(db,col,_id,['config','logging','deleted_messages'])
				"""bool"""
				self.edited_messages = MongoObject(db,col,_id,['config','logging','edited_messages'])
				"""bool"""
				self.filtered_messages = MongoObject(db,col,_id,['config','logging','filtered_messages'])
				"""bool"""
				self.member_join = MongoObject(db,col,_id,['config','logging','member_join'])
				"""bool"""
				self.member_leave = MongoObject(db,col,_id,['config','logging','member_leave'])
				"""bool"""
				self.log_bots = MongoObject(db,col,_id,['config','logging','log_bots'])
				"""bool"""

		class ___tts(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.channel = MongoObject(db,col,_id,['config','tts','channel'])
				"""int"""
				self.auto_join = MongoObject(db,col,_id,['config','tts','auto_join'])
				"""bool"""
				self.max_message_length = MongoObject(db,col,_id,['config','tts','max_message_length'])
				"""int"""
				self.voice = MongoObject(db,col,_id,['config','tts','voice'])
				"""str"""
				self.read_name = MongoObject(db,col,_id,['config','tts','read_name'])
				"""bool"""

		class ___qotd(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.enabled = MongoObject(db,col,_id,['config','qotd','enabled'])
				"""bool"""
				self.channel = MongoObject(db,col,_id,['config','qotd','channel'])
				"""int"""
				self.spawn_threads = MongoObject(db,col,_id,['config','qotd','spawn_threads'])
				"""bool"""
				self.delete_after = MongoObject(db,col,_id,['config','qotd','delete_after'])
				"""bool"""

		class ___talking_stick(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.enabled = MongoObject(db,col,_id,['config','talking_stick','enabled'])
				"""bool"""
				self.channel = MongoObject(db,col,_id,['config','talking_stick','channel'])
				"""int"""
				self.role = MongoObject(db,col,_id,['config','talking_stick','role'])
				"""int"""
				self.limit = MongoObject(db,col,_id,['config','talking_stick','limit'])
				"""int"""

		class ___auto_responses(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.enabled = MongoObject(db,col,_id,['config','auto_responses','enabled'])
				"""str"""
				self.cooldown = MongoObject(db,col,_id,['config','auto_responses','cooldown'])
				"""int"""
				self.cooldown_per_user = MongoObject(db,col,_id,['config','auto_responses','cooldown_per_user'])
				"""bool"""

		class ___dad_bot(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.enabled = MongoObject(db,col,_id,['config','dad_bot','enabled'])
				"""str"""
				self.cooldown = MongoObject(db,col,_id,['config','dad_bot','cooldown'])
				"""int"""
				self.cooldown_per_user = MongoObject(db,col,_id,['config','dad_bot','cooldown_per_user'])
				"""bool"""

	class ___data(MongoObject):
		def __init__(self,db,col,_id,path) -> None:
			super().__init__(db,col,_id,path)
			self.leaderboards = self.___leaderboards(db,col,_id,['data','leaderboards'])
			"""dict[str,dict]"""
			self.sauce = self.___sauce(db,col,_id,['data','sauce'])
			"""dict[str,dict]"""
			self.logging = self.___logging(db,col,_id,['data','logging'])
			"""dict[str,dict]"""
			self.qotd = self.___qotd(db,col,_id,['data','qotd'])
			"""dict[str,dict]"""
			self.talking_stick = self.___talking_stick(db,col,_id,['data','talking_stick'])
			"""dict[str,dict]"""
			self.auto_responses = self.___auto_responses(db,col,_id,['data','auto_responses'])
			"""dict[str,dict]"""
			self.dad_bot = self.___dad_bot(db,col,_id,['data','dad_bot'])
			"""dict[str,dict]"""
			self.hide_commands = self.___hide_commands(db,col,_id,['data','hide_commands'])
			"""dict[str,dict]"""
			self.tts = self.___tts(db,col,_id,['data','tts'])
			"""dict[str,dict]"""

		class ___leaderboards(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.messages = MongoObject(db,col,_id,['data','leaderboards','messages'])
				"""dict[str,int]"""
				self.sticks = MongoObject(db,col,_id,['data','leaderboards','sticks'])
				"""dict[str,int]"""

		class ___sauce(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.key = MongoObject(db,col,_id,['data','sauce','key'])
				"""str"""

		class ___logging(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.last_history = MongoObject(db,col,_id,['data','logging','last_history'])
				"""str"""

		class ___qotd(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.last = MongoObject(db,col,_id,['data','qotd','last'])
				"""list[int]"""
				self.nextup = MongoObject(db,col,_id,['data','qotd','nextup'])
				"""list[str]"""
				self.pool = MongoObject(db,col,_id,['data','qotd','pool'])
				"""list[str]"""
				self.asked = MongoObject(db,col,_id,['data','qotd','asked'])
				"""list[str]"""

		class ___talking_stick(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.current_stick = MongoObject(db,col,_id,['data','talking_stick','current_stick'])
				"""int"""
				self.active = MongoObject(db,col,_id,['data','talking_stick','active'])
				"""list[int]"""

		class ___auto_responses(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.whitelist = MongoObject(db,col,_id,['data','auto_responses','whitelist'])
				"""list[int]"""
				self.blacklist = MongoObject(db,col,_id,['data','auto_responses','blacklist'])
				"""list[int]"""
				self.custom = MongoObject(db,col,_id,['data','auto_responses','custom'])
				"""dict[str,dict]"""
				self.disabled = MongoObject(db,col,_id,['data','auto_responses','disabled'])
				"""list[str]"""

		class ___dad_bot(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.whitelist = MongoObject(db,col,_id,['data','dad_bot','whitelist'])
				"""list[int]"""
				self.blacklist = MongoObject(db,col,_id,['data','dad_bot','blacklist'])
				"""list[int]"""

		class ___hide_commands(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.whitelist = MongoObject(db,col,_id,['data','hide_commands','whitelist'])
				"""list[int]"""
				self.blacklist = MongoObject(db,col,_id,['data','hide_commands','blacklist'])
				"""list[int]"""

		class ___tts(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.usage = MongoObject(db,col,_id,['data','tts','usage'])
				"""int"""
				self.banned_users = MongoObject(db,col,_id,['data','tts','banned_users'])
				"""list[int]"""

class Log(MongoObject):
	def __init__(self,db,col:Collection,_id) -> None:
		super().__init__(db,col,_id,[])
		"""Collection\n\nraw mongodb collection"""
		self._id = MongoObject(db,col,_id,['_id'])
		"""int"""
		self.ts = MongoObject(db,col,_id,['ts'])
		"""float"""
		self.dt = MongoObject(db,col,_id,['dt'])
		"""dt"""
		self.dev = MongoObject(db,col,_id,['dev'])
		"""bool"""
		self.type = MongoObject(db,col,_id,['type'])
		"""str"""
		self.log = MongoObject(db,col,_id,['log'])
		"""str"""
		self.guild = MongoObject(db,col,_id,['guild'])
		"""int"""
		self.channel = MongoObject(db,col,_id,['channel'])
		"""int"""
		self.author = MongoObject(db,col,_id,['author'])
		"""int"""
		self.data = MongoObject(db,col,_id,['data'])
		"""dict[str,Any]"""

class Message(MongoObject):
	def __init__(self,db,col:Collection,_id) -> None:
		super().__init__(db,col,_id,[])
		"""Collection\n\nraw mongodb collection"""
		self._id = MongoObject(db,col,_id,['_id'])
		"""int"""
		self.author = MongoObject(db,col,_id,['author'])
		"""int"""
		self.guild = MongoObject(db,col,_id,['guild'])
		"""int"""
		self.channel = MongoObject(db,col,_id,['channel'])
		"""int"""
		self.reply_to = MongoObject(db,col,_id,['reply_to'])
		"""int"""
		self.deleted_by = MongoObject(db,col,_id,['deleted_by'])
		"""int"""
		self.log_messages = MongoObject(db,col,_id,['log_messages'])
		"""list[int]"""
		self.logs = MongoObject(db,col,_id,['logs'])
		"""list[list[int,str,str]]"""
		self.attachments = MongoObject(db,col,_id,['attachments'])
		"""list[str]"""

class Poll(MongoObject):
	def __init__(self,db,col:Collection,_id) -> None:
		super().__init__(db,col,_id,[])
		"""Collection\n\nraw mongodb collection"""
		self._id = MongoObject(db,col,_id,['_id'])
		"""int\n\nassociated message id"""
		self.options = MongoObject(db,col,_id,['options'])
		"""dict[str,dict]"""
		self.voters = MongoObject(db,col,_id,['voters'])
		"""dict[str,str]"""
		self.embed = self.___embed(db,col,_id,['embed'])
		"""dict[str,str|int]"""

	class ___embed(MongoObject):
		def __init__(self,db,col,_id,path) -> None:
			super().__init__(db,col,_id,path)
			self.title = MongoObject(db,col,_id,['embed','title'])
			"""str"""
			self.description = MongoObject(db,col,_id,['embed','description'])
			"""str"""
			self.color = MongoObject(db,col,_id,['embed','color'])
			"""int"""

class RoleMenu(MongoObject):
	def __init__(self,db,col:Collection,_id) -> None:
		super().__init__(db,col,_id,[])
		"""Collection\n\nraw mongodb collection"""
		self._id = MongoObject(db,col,_id,['_id'])
		"""int\n\nassociated message id"""
		self.placeholder = MongoObject(db,col,_id,['placeholder'])
		"""str"""
		self.options = MongoObject(db,col,_id,['options'])
		"""dict[str,dict]"""

class StatusLog(MongoObject):
	def __init__(self,db,col:Collection,_id) -> None:
		super().__init__(db,col,_id,[])
		"""Collection\n\nraw mongodb collection"""
		self._id = MongoObject(db,col,_id,['_id'])
		"""int"""
		self.timestamp = MongoObject(db,col,_id,['timestamp'])
		"""str|int"""
		self.stats = self.___stats(db,col,_id,['stats'])
		"""dict[str,int]"""

	class ___stats(MongoObject):
		def __init__(self,db,col,_id,path) -> None:
			super().__init__(db,col,_id,path)
			self.db_reads = MongoObject(db,col,_id,['stats','db_reads'])
			"""int"""
			self.db_writes = MongoObject(db,col,_id,['stats','db_writes'])
			"""int"""
			self.messages_seen = MongoObject(db,col,_id,['stats','messages_seen'])
			"""int"""
			self.commands_used = MongoObject(db,col,_id,['stats','commands_used'])
			"""int"""

class User(MongoObject):
	def __init__(self,db,col:Collection,_id) -> None:
		super().__init__(db,col,_id,[])
		"""Collection\n\nraw mongodb collection"""
		self._id = MongoObject(db,col,_id,['_id'])
		"""int|str\n\ndiscord id or pluralkit uuid"""
		self.username = MongoObject(db,col,_id,['username'])
		"""str\n\ndiscord username or pluralkit username"""
		self.discriminator = MongoObject(db,col,_id,['discriminator'])
		"""str\n\ndiscord disciminator"""
		self.messages = MongoObject(db,col,_id,['messages'])
		"""int\n\ntotal number of seen messages"""
		self.bot = MongoObject(db,col,_id,['bot'])
		"""bool\n\nwhether the user is a bot or not"""
		self.pluralkit = MongoObject(db,col,_id,['pluralkit'])
		"""bool\n\nwhether the user is a pluralkit member"""
		self.config = self.___config(db,col,_id,['config'])
		"""dict[str,dict]\n\nuser configuration options"""
		self.data = self.___data(db,col,_id,['data'])
		"""dict[str,dict]\n\nuser data storage"""

	class ___config(MongoObject):
		def __init__(self,db,col,_id,path) -> None:
			super().__init__(db,col,_id,path)
			self.general = self.___general(db,col,_id,['config','general'])
			"""dict[str,bool]\n\nconfig general category"""
			self.tts = self.___tts(db,col,_id,['config','tts'])
			"""dict[str,str|bool|float]\n\nconfig tts category"""

		class ___general(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.ignored = MongoObject(db,col,_id,['config','general','ignored'])
				"""bool"""
				self.no_track = MongoObject(db,col,_id,['config','general','no_track'])
				"""bool"""
				self.hide_commands = MongoObject(db,col,_id,['config','general','hide_commands'])
				"""bool"""
				self.talking_stick = MongoObject(db,col,_id,['config','general','talking_stick'])
				"""bool"""

		class ___tts(MongoObject):
			def __init__(self,db,col,_id,path) -> None:
				super().__init__(db,col,_id,path)
				self.mode = MongoObject(db,col,_id,['config','tts','mode'])
				"""str"""
				self.name = MongoObject(db,col,_id,['config','tts','name'])
				"""str"""
				self.voice = MongoObject(db,col,_id,['config','tts','voice'])
				"""str"""
				self.transcription = MongoObject(db,col,_id,['config','tts','transcription'])
				"""bool"""
				self.speaking_rate = MongoObject(db,col,_id,['config','tts','speaking_rate'])
				"""float"""

	class ___data(MongoObject):
		def __init__(self,db,col,_id,path) -> None:
			super().__init__(db,col,_id,path)
			self.au = MongoObject(db,col,_id,['data','au'])
			"""list[str]\n\ndata found auto responses"""