from discord import slash_command,ApplicationContext,Embed,RawReactionActionEvent,Message
from pymongo.collection import Collection
from discord.errors import Forbidden
from discord.ext.commands import Cog
from client import Client

"""hardcoded garbage because i don't wanna remake the role menu"""
DISBOARDERS_ROLE = 306170169942736916
REACTION_MESSAGES = [
	905127092017049650,
	905129214771077150,
	909190775848448010]
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
REQUIRES_DISBOARDER = [
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

class tet_stupid_reaction_roles_bullshit(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client
		self.db:Collection = self.client.db._client.reaction_roles_bullshit
	
	@Cog.listener()
	async def on_message(self,message:Message) -> None:
		if message.guild is None: return
		if DISBOARDERS_ROLE not in [r.id for r in message.author.roles]: return
		if (doc:=await self.db.find_one({'_id':message.author.id})) is None: return
		if (role:=doc.get('role',None)) is None: return
		
		await message.author.add_roles(message.guild.get_role(role),reason='reaction role add')
		await self.db.delete_one({'_id':message.author.id})

	@Cog.listener()
	async def on_raw_reaction_add(self,payload:RawReactionActionEvent) -> None:
		if payload.message_id not in REACTION_MESSAGES or payload.guild_id is None: return
		reaction = payload.emoji.name if payload.emoji.id is None else payload.emoji.id
		role_id = ROLES.get(reaction,None)
		if role_id is None: return
		try: guild = self.client.get_guild(payload.guild_id) or await self.client.fetch_guild(payload.guild_id)
		except Forbidden: return
		if guild is None: return
		try: member = payload.member or guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
		except Forbidden: return
		if member is None: return
		if role_id in REQUIRES_DISBOARDER and DISBOARDERS_ROLE not in [r.id for r in member.roles]:
			await self.db.update_one({'_id':member.id},{'role':role_id},upsert=True)
			return
		role = guild.get_role(role_id)
		match payload.event_type:
			case 'REACTION_ADD':
				if role_id in REQUIRES_DISBOARDER: await member.remove_roles(*[guild.get_role(ROLES.get(r)) for r in REQUIRES_DISBOARDER])
				await member.add_roles(role,reason='reaction role add')
			case 'REACTION_REMOVE':
				await member.remove_roles(role,reason='reaction role remove')

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


def setup(client:Client) -> None:
	client._extloaded()
	client.add_cog(tet_commands(client))
	client.add_cog(tet_stupid_reaction_roles_bullshit(client))