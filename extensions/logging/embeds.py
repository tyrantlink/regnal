from discord import Embed,Message,Member,AuditLogEntry
from datetime import datetime
from time import time


class EditLogEmbed(Embed):
	def __init__(self,after:Message,before:Message=None) -> None:
		super().__init__()
		time_diff = (
			after.edited_at or
			datetime.now()
			).timestamp()-(
				(before.edited_at or before.created_at)
				if before is not None else
				after.created_at
		).timestamp()

		match time_diff:
			case _ if time_diff < 1: diff_string = f'{time_diff*1000:.2f} milliseconds'
			case _ if time_diff < 60: diff_string = f'{time_diff:.2f} seconds'
			case _ if time_diff < 3600: diff_string = f'{time_diff/60:.2f} minutes'
			case _ if time_diff < 86400: diff_string = f'{time_diff/3600:.2f} hours'
			case _: diff_string = f'{time_diff/86400:.2f} days'

		self.description = '\n'.join(
			[
				after.author.mention,
				f'edited a [message](<{after.jump_url}>)',
				f'in {after.channel.mention}',
				f'after {diff_string}'
			]
		)
		self.color = 0xffff69
		self.set_author(name=after.author.name,icon_url=after.author.display_avatar.url)
		self.add_field(
			name=f'ORIGINAL <t:{int((after.edited_at or after.created_at).timestamp())}:t>',inline=False,
			value=(
				(
					before.content
					if len(before.content) <= 1024
					else '`message content too long, provided in additional embed`'
				) or '`no content`')
				if before is not None else
				'`original message not in cache; may be too old`')
		self.add_field(
			name=f'EDITED <t:{int((after.edited_at or datetime.now()).timestamp())}:t>',
			value=(
				after.content if len(after.content) <= 1024 else '`message content too long, provided in additional embed`' or
				'`no content`'),inline=False)
		self.set_footer(text=after.id)
		self.additional_embeds = []
		if before and len(before.content) > 1024:
			self.additional_embeds.append(Embed(
				title='original message content',
				description=before.content,
				color=0xffff69))
		if len(after.content) > 1024:
			self.additional_embeds.append(Embed(
				title='edited message content',
				description=after.content,
				color=0xffff69))

class DeleteLogEmbedFromID(Embed):
	def __init__(self,message_id:int,channel_id:int,author:Member=None,deleter:Member=None) -> None:
		super().__init__()
		self.description = f'''an uncached message by {
			author.mention if author is not None else "an unknown user"} was deleted in <#{
				channel_id}> by {deleter.mention if deleter is not None else "an unknown user"}'''
		self.description = '\n'.join(
			[
				f'a uncached message by {author.mention if author is not None else "an unknown user"}',
				f'was **deleted** in <#{channel_id}>',
				f'by {deleter.mention if deleter is not None else "an unknown user"}'
			]
		)
		self.color = 0xff6969
		if author is not None: self.set_author(name=author.name,icon_url=author.display_avatar.url)
		self.add_field(name=f'DELETED <t:{int(time())}:t>',value='`original message not in cache; may be too old`',inline=False)
		self.set_footer(text=message_id)

class DeleteLogEmbedFromMessage(Embed):
	def __init__(self,message:Message,deleter:Member) -> None:
		super().__init__()
		reference_message = message.reference.resolved if message.reference else None
		self.description = '\n'.join(
			[
				m for m in
				[
					f'a message by {message.author.mention}',
					f'replying to {reference_message.author.mention}\'s [message](<{reference_message.jump_url}>)'
						if reference_message
						else None,
					f'was **deleted** in {message.channel.mention}',
					f'by {deleter.mention}'
				]
				if m is not None
			]
		)
		self.color = 0xff6969
		self.set_author(name=message.author.name,icon_url=message.author.display_avatar.url)
		self.add_field(
			name=f'DELETED <t:{int(time())}:t>',
			value=(message.content if len(message.content) <= 1024 else '`message content too long, provided in additional embed`') or '`no content`',inline=False)
		if message.attachments: self.add_field(name='ATTACHMENTS',value='\n'.join([f'[{attachment.filename}]({attachment.url})' for attachment in message.attachments]),inline=False)
		self.set_footer(text=message.id)
		self.additional_embeds = []
		if len(message.content) > 1024:
			self.additional_embeds.append(Embed(
				title='message content',
				description=message.content,
				color=0xff6969))

class _BaseMemberStateUpdateLogEmbed(Embed):
	def __init__(self,member:Member,color:int) -> None:
		super().__init__()
		self.description = member.mention
		self.color = color
		self.add_field(name='username',value=member.name,inline=True)
		self.set_thumbnail(url=member.display_avatar.url)
		self.set_footer(text=member.id)

class MemberJoinLogEmbed(_BaseMemberStateUpdateLogEmbed):
	def __init__(self,member:Member) -> None:
		super().__init__(member,0x69ff69)
		self.description += ' joined the server!'
		self.add_field(name='join time',value=f'<t:{int(member.joined_at.timestamp())}:f>',inline=False)

class MemberLeaveLogEmbed(_BaseMemberStateUpdateLogEmbed):
	def __init__(self,member:Member) -> None:
		super().__init__(member,0xff6969)
		self.description += ' left the server!'
		if member.nick:
			self.add_field(name='nickname',value=member.nick,inline=True)
		self.add_field(name='join time',value=f'<t:{int(member.joined_at.timestamp())}:f>',inline=False)
		self.add_field(name='leave time',value=f'<t:{int(time())}:f>',inline=False)
		if member.roles[1:]:
			self.add_field(name='roles',value=' '.join([role.mention for role in member.roles[1:]]),inline=False)

class _MemberBanUpdateLogEmbed(Embed):
	def __init__(self,member:Member,audit_log:AuditLogEntry=None) -> None:
		super().__init__()
		self.description = member.mention
		self.color = 0xff6969
		self.add_field(name='username',value=member.name,inline=False)
		self.set_thumbnail(url=member.display_avatar.url)
		self.set_footer(text=member.id)
		if audit_log is None: return
		self.set_author(name=audit_log.user.name,icon_url=audit_log.user.display_avatar.url)
		self.add_field(name='reason',value=audit_log.reason or '`no reason provided`',inline=False)

class MemberBanLogEmbed(_MemberBanUpdateLogEmbed):
	def __init__(self,member:Member,audit_log:AuditLogEntry) -> None:
		super().__init__(member,audit_log)
		self.description += ' was banned from the server!'
		self.add_field(name='ban time',value=f'<t:{int(time())}:f>',inline=False)

class MemberUnbanLogEmbed(_MemberBanUpdateLogEmbed):
	def __init__(self,member:Member,audit_log:AuditLogEntry) -> None:
		super().__init__(member,audit_log)
		self.description += ' was unbanned from the server!'
		self.add_field(name='unban time',value=f'<t:{int(time())}:f>',inline=False)