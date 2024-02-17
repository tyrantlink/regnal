from discord import Message,slash_command,ApplicationContext,message_command
from utils.pycord_classes import SubCog
from .embed import au_info_embed


class ExtensionAutoResponsesCommands(SubCog):
	@slash_command(
			name='auto_responses',
			description='browse auto responses you\'ve found',
			guild_only=True)
	async def slash_auto_responses(self,ctx:ApplicationContext) -> None:
		print('in app command')

	@message_command(
		name='au info',
		guild_only=True)
	async def message_au_info(self,ctx:ApplicationContext,message:Message) -> None:
		log = await self.client.db.log(message.id)
		if log is None or (au_id:=log.data.get('au',None)) is None:
			await ctx.response.send_message('this message is not an auto response!',ephemeral=True)
			return
		au = self.client.au.get(au_id)
		if au is None:
			await ctx.response.send_message('auto response not found!',ephemeral=True)
			return
		_user = await self.client.db.user(ctx.author.id)
		extra_info = _user.config.general.developer_mode if _user else False
		embed_color = await self.client.helpers.embed_color(ctx.guild_id)
		embed = au_info_embed(au,embed_color,extra_info)

		await ctx.response.send_message(embed=embed,ephemeral=await self.client.helpers.ephemeral(ctx))