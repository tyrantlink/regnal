from discord import SlashCommandGroup,Permissions,Option,ApplicationContext,Embed
from utils.db.documents.guild import GuildDataQOTDQuestion
from .__subcog__ import QOTDSubCog

class ExtensionQOTDCommands(QOTDSubCog):
	qotd = SlashCommandGroup('qotd','question of the day commands')

	@qotd.command(
		name='custom',
		description='ask a custom question of the day!',
		guild_only=True,default_member_permissions=Permissions(manage_messages=True),
		options=[
			Option(str,name='question',description='question to be asked',max_length=256)])
	async def ask_custom(self,ctx:ApplicationContext,question:str) -> None:
		guild_doc = await self.client.db.guild(ctx.guild.id)
		if not guild_doc.config.qotd.enabled:
			await ctx.response.send_message('QOTD is not enabled in this server!',ephemeral=True)
			return
		if guild_doc.config.qotd.channel is None:
			await ctx.response.send_message('QOTD channel is not set in this server!',ephemeral=True)
			return
		question_data = GuildDataQOTDQuestion(
			question=question,
			author=ctx.author.display_name,
			icon=ctx.author.avatar.url)
		guild_doc.data.qotd.nextup.append(question_data)
		await guild_doc.save()
		embed = Embed(
			title='custom question queued!',
			description=f'your custom question will be asked {"next" if len(guild_doc.data.qotd.nextup) == 1 else f"in {len(guild_doc.data.qotd.nextup)} days"}!',
			color=await self.client.helpers.embed_color(ctx.guild.id))
		embed.add_field(name='question',value=question)
		await ctx.response.send_message(embed=embed,ephemeral=True)
		
		await self.log_ask_custom(ctx.author,question)