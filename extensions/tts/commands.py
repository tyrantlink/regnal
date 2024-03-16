from discord import SlashCommandGroup,Permissions,Option,ApplicationContext,Embed
from .subcog import ExtensionTTSSubCog


class ExtensionTTSCommands(ExtensionTTSSubCog):
	tts = SlashCommandGroup('tts','text-to-speech commands')

	@tts.command(
		name = 'join',
		description = 'join the current voice channel',
		guild_only = True)
	async def join(self,ctx:ApplicationContext) -> None:
		if ctx.author.voice is None:
			error = ValueError('you are not in a voice channel!')
			error.add_note('suppress')
			raise error
		await self.join_channel(ctx.author.voice.channel)
		tts_channels = '\n'+'\n'.join([
			f'<#{channel_id}>'
			for channel_id in
			(await self.client.db.guild(ctx.guild.id)).config.tts.channels])
		config_command = self.client.helpers.handle_cmd_ref('{cmd_ref[config]}')
		await ctx.response.send_message(
			embed = Embed(
				title = f'connected to {ctx.guild.voice_client.channel.mention}',
				description = f'''- by default, i will only read you messages if you're muted, you can change this with {config_command}
													- prepend messages with "-" and i won't read them.
													- use {config_command} and enable tts auto join to have me join automagically when you send a message.
													- you must send a message in the active voice channel{
														' or any of the following channels'
														if tts_channels else ''
													} if you want it read.
													{tts_channels}'''.replace('\t',''),
				color = await self.client.helpers.embed_color(ctx.guild.id)),
			ephemeral = await self.client.helpers.ephemeral(ctx))

	@tts.command(
		name = 'leave',
		description = 'leave the current voice channel',
		guild_only = True)
	async def leave(self,ctx:ApplicationContext) -> None:
		await self.disconnect(ctx.guild.id)
		await ctx.response.send_message(
			embed = Embed(
				title = 'disconnected',
				description = 'have fun~',
				color = await self.client.helpers.embed_color(ctx.guild.id)))