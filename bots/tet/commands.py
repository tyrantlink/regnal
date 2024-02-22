from discord import slash_command,ApplicationContext
from utils.pycord_classes import SubCog
from discord.embeds import Embed


class BotExtensionTetCommands(SubCog):
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