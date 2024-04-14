from discord import TextChannel,Message,Member,Guild,AuditLogEntry
from utils.pycord_classes import SubCog
from client import Client

class ExtensionLoggingSubCog(SubCog):
	def __init__(self) -> None:
		self.client:Client
		self.cached_counts:dict
		super().__init__()

	async def get_logging_channel(self,guild_id:int) -> TextChannel|None: ...
	async def from_raw_edit(self,data:dict) -> Message|None: ...
	async def find_deleter_from_message(self,message:Message) -> Member: ...
	async def find_deleter_from_id(self,message:int,guild:Guild,channel_id:int) -> tuple[Member,Member]|tuple[None,None]: ...
	async def find_ban_entry(self,guild:Guild,user_id:int,unban:bool=False) -> AuditLogEntry|None: ...
	async def deleted_by_pk(self,message_id:int,delay:int=2) -> bool: ...