from discord import Embed,Message,Member
from time import time


class EditLogEmbed(Embed):
	def __init__(self,after:Message,before:Message=None) -> None:
		super().__init__()
		self.description = f'{after.author.mention} edited a [message](<{after.jump_url}>) in {after.channel.mention}'
		self.color = 0xffff69
		self.set_author(name=after.author.name,icon_url=after.author.avatar.url)
		self.add_field(
			name=f'ORIGINAL <t:{int((after.edited_at or after.created_at).timestamp())}:t>',inline=False,
			value=(before.content or '`no content`') if before is not None else '`original message not in cache; may be too old`')
		self.add_field(
			name=f'EDITED <t:{int(after.edited_at.timestamp())}:t>',
			value=after.content or '`no content`',inline=False)
		self.set_footer(text=f'message: {after.id}\nauthor: {after.author.id}')
	
class DeleteLogEmbedFromID(Embed):
	def __init__(self,message_id:int,channel_id:int,guild_id:int,author:Member=None,deleter:Member=None) -> None:
		super().__init__()
		self.description = f'''an uncached message by {
			author.mention if author is not None else "an unknown user"} was deleted by {
			deleter.mention if deleter is not None else "an unknown user"}'''
		self.color = 0xff6969
		if author is not None: self.set_author(name=author.name,icon_url=author.avatar.url)
		self.add_field(name=f'DELETED <t:{int(time())}:t>',value='`original message not in cache; may be too old`',inline=False)
		self.set_footer(
			text=f'message: {message_id}\nauthor: {author.id if author is not None else "unknown"}\ndeleter: {deleter.id if deleter is not None else "unknown"}',
			icon_url=deleter.avatar.url if deleter is not None else None)

class DeleteLogEmbedFromMessage(Embed):
	def __init__(self,message:Message,deleter:Member) -> None:
		super().__init__()
		self.description = f'''a [message](<{message.jump_url}>) by {
			message.author.mention} was deleted in {message.channel.mention} by {deleter.mention}'''
		self.color = 0xff6969
		self.set_author(name=message.author.name,icon_url=message.author.avatar.url)
		self.add_field(name=f'DELETED <t:{int(time())}:t>',value=message.content or '`no content`',inline=False)
		if message.attachments: self.add_field(name='ATTACHMENTS',value='\n'.join([f'[{attachment.filename}]({attachment.url})' for attachment in message.attachments]),inline=False)
		self.set_footer(
			text=f'message: {message.id}\nauthor: {message.author.id}\ndeleter: {deleter.id}',
			icon_url=deleter.avatar.url)