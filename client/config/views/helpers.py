# helper functions when changing config options
from utils.db.documents.user import User
from discord.abc import GuildChannel
from discord import Member
from discord.enums import ChannelType
from .enums import ValidOption
from typing import Any


async def handle_user_no_track(user:User) -> None:
	user.data.statistics.messages = {}
	user.data.statistics.commands = {}
	user.data.statistics.tts_usage = 0
	user.data.auto_responses.found = []
	await user.save_changes()

async def validate_qotd_channel(channel:GuildChannel,self:Member) -> tuple[ValidOption,str]:
	if channel.type not in [
		ChannelType.text,
		ChannelType.forum
	]: return (ValidOption.false,'channel must be a text channel or dm')

	if not channel.permissions_for(self).send_messages:
		return (ValidOption.false,'i don\'t have permission to send messages in that channel\nthis requires the `Send Messages` permission')

	if not channel.permissions_for(self).embed_links:
		return (ValidOption.false,'i don\'t have permission to embed links in that channel\nthis requires the `Embed Links` permission')
	
	if channel.type == ChannelType.text:
		return (ValidOption.true,'')
	
	if not channel.permissions_for(self).create_public_threads:
		return (ValidOption.false,'i don\'t have permission to create threads in that channel\nthis requires the `Create Posts` permission')

	if not channel.permissions_for(self).manage_threads:
		return (ValidOption.false,'i don\'t have permission to manage threads in that channel\nthis requires the `Manage Posts` permission')
	
	if not channel.permissions_for(self).manage_messages:
		return (ValidOption.false,'i don\'t have permission to pin messages in that channel\n\nthis requires the `Manage Messages` permission')
	
	return (ValidOption.true,'')
	
