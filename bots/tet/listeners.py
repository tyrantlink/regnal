from discord import RawReactionActionEvent,Member,Forbidden
from utils.pycord_classes import SubCog
from discord.ext.commands import Cog


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

class BotExtensionTetListeners(SubCog):
	@Cog.listener('on_raw_reaction_add')
	@Cog.listener('on_raw_reaction_remove')
	async def on_raw_reaction_update(self,payload:RawReactionActionEvent) -> None:
		if payload.message_id not in REACTION_MESSAGES: return
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
				if reaction in LIMITED_TO_ONE: await member.remove_roles(*[guild.get_role(ROLES.get(r)) for r in LIMITED_TO_ONE if member.get_role(ROLES.get(r)) is not None],atomic=False,reason='reaction role add')
				await member.add_roles(guild.get_role(role_id),reason='reaction role add')
			case 'REACTION_REMOVE':
				await member.remove_roles(guild.get_role(role_id),reason='reaction role remove')