from discord import slash_command,Embed,RawReactionActionEvent,Member
from utils.classes import ApplicationContext
from discord.ext.commands import Cog
from discord.errors import Forbidden
from client import Client

"""hardcoded garbage because i don't wanna remake the role menu"""
DISBOARDERS_ROLE = 306170169942736916
REACTION_MESSAGES = [905127092017049650,905129214771077150,909190775848448010]
ROLES = {
	318046820750196736:306168371806994433,
	317959303350976513:306168385555791872,
	345993133584154625:306168400915464192,
	420698827742380032:308873033592995842,
	317987048546107392:308872540183592962,
	318293352745271298:308873006946582528,
	334049957248106496:308871977542877184,
	318371640184537091:354311179193024513,
	319052644327096320:308872442624081920,
	338198310160695307:339144100987273228,
	828429490756911145:339144386111864843,
	418650515153354762:339144981493055500,
	862802371448275024:354636785998888961,
	'❄️':788834198940549160,'📖':862874142855659550,
	'🛠️':862873988103667722,'🔈':862874115357409340,
	'🎵':902636085472006155,'🔍':1046582058002161765,
	'♂️':909164111265415278,'♀️':909163765306622063,
	'⚧':909164269768155156}
LIMITED_TO_ONE = [
	318046820750196736,
	317959303350976513,
	345993133584154625,
	420698827742380032,
	317987048546107392,
	318293352745271298,
	334049957248106496,
	318371640184537091,
	319052644327096320,
	338198310160695307,
	828429490756911145,
	418650515153354762,
	862802371448275024,
	'❄️']

class tet_stupid_dyno_replacement_bullshit(Cog):
	"""will be removed once onboarding is fully public, this is just a temp solution for replacing dyno"""
	def __init__(self,client:Client) -> None:
		self.client = client

	@Cog.listener('on_raw_reaction_add')
	@Cog.listener('on_raw_reaction_remove')
	async def on_raw_reaction_add(self,payload:RawReactionActionEvent) -> None:
		if payload.message_id not in REACTION_MESSAGES or payload.guild_id is None: return
		reaction = payload.emoji.name if payload.emoji.id is None else payload.emoji.id
		role_id = ROLES.get(reaction,None)
		if role_id is None: return
		try: guild = self.client.get_guild(payload.guild_id) or await self.client.fetch_guild(payload.guild_id)
		except Forbidden: return
		if guild is None: return
		try:
			member = payload.member or guild.get_member(payload.user_id)
			if not isinstance(member,Member): member = await guild.fetch_member(payload.user_id)
		except Forbidden: return
		if member is None: return
		match payload.event_type:
			case 'REACTION_ADD':
				await self.client.log.info(f'reaction role add on {member}',roles=[guild.get_role(ROLES.get(r)).name for r in ROLES.keys() if member.get_role(ROLES.get(r)) is not None])
				if reaction in LIMITED_TO_ONE: await member.remove_roles(*[guild.get_role(ROLES.get(r)) for r in LIMITED_TO_ONE if member.get_role(ROLES.get(r)) is not None],atomic=False,reason='reaction role add')
				await member.add_roles(guild.get_role(role_id),reason='reaction role add')
			case 'REACTION_REMOVE':
				await self.client.log.info(f'reaction role remove on {member}',roles=[guild.get_role(ROLES.get(r)).name for r in ROLES.keys() if member.get_role(ROLES.get(r)) is not None])
				await member.remove_roles(guild.get_role(role_id),reason='reaction role remove')

class tet_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	@slash_command(
		name='aschente',
		description='you\'ve read the rules',
		guild_ids=[305627343895003136])
	async def slash_aschente(self,ctx:ApplicationContext) -> None:
		embed = Embed(color=0xf9b5fa)
		role  = ctx.guild.get_role(306153845048737792)
		if ctx.author.get_role(role.id):
			embed.set_author(name='you already had the role, so i didn\'t do anything',icon_url=self.client.user.display_avatar.url)
			await ctx.response.send_message(embed=embed,ephemeral=True)
			return
		await ctx.author.add_roles(role,reason='used /aschente')
		embed.set_author(name='welcome to disboard~!',icon_url=self.client.user.display_avatar.url)
		await ctx.response.send_message(embed=embed,ephemeral=True)

	@slash_command(
		name='lewd',
		description='sus',
		guild_ids=[305627343895003136])
	async def slash_lewd(self,ctx:ApplicationContext) -> None:
		embed = Embed(color=0xf9b5fa)
		role  = ctx.guild.get_role(845538867784450049)
		if ctx.author.get_role(306153845048737792) is None:
			embed.color = 0xff6969
			embed.set_author(name='you must be a member before using this command!',icon_url=self.client.user.display_avatar.url)
			await ctx.response.send_message(embed=embed,ephemeral=True)
			return
		if ctx.author.get_role(role.id):
			embed.set_author(name='you already had the role, so i didn\'t do anything',icon_url=self.client.user.display_avatar.url)
			await ctx.response.send_message(embed=embed,ephemeral=True)
			return
		await ctx.author.add_roles(role,reason='used /lewd')
		embed.set_author(name='sus')
		embed.description = '<:IzunaStare:319616840693317632>'
		await ctx.response.send_message(embed=embed,ephemeral=True)

	@slash_command(
		name='notlewd',
		description='less sus',
		guild_ids=[305627343895003136])
	async def slash_notlewd(self,ctx:ApplicationContext) -> None:
		embed = Embed(color=0xf9b5fa)
		role  = ctx.guild.get_role(845538867784450049)
		if ctx.author.get_role(306153845048737792) is None:
			embed.color = 0xff6969
			embed.set_author(name='you must be a member before using this command!',icon_url=self.client.user.display_avatar.url)
			await ctx.response.send_message(embed=embed,ephemeral=True)
			return
		if not ctx.author.get_role(role.id):
			embed.set_author(name='you didn\'t have the role, so i didn\'t do anything',icon_url=self.client.user.display_avatar.url)
			await ctx.response.send_message(embed=embed,ephemeral=True)
			return
		await ctx.author.remove_roles(role,reason='used /notlewd')
		embed.set_author(name='you\'re no longer sus')
		await ctx.response.send_message(embed=embed,ephemeral=True)


def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(tet_commands(client))
	client.add_cog(tet_stupid_dyno_replacement_bullshit(client))