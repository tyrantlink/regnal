from discord import Cog,slash_command,ApplicationContext,Embed
if not 'TYPE_HINT': from client import Client


class BaseCommands(Cog):
	def __init__(self,client:"Client") -> None:
		self.client = client

	@slash_command(
		name='ping',
		description='pong')
	async def slash_ping(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(f'pong! {round(self.client.latency*100,1)}ms',ephemeral=await self.client.helpers.ephemeral(ctx))
	
	@slash_command(
		name='donate',
		description='pls donate am broke')
	async def slash_donate(self,ctx:ApplicationContext) -> None:
		embed = Embed(
			description='uhhh, this is for donations, i refuse to lock any features behind a paywall, at best you can donate so i\'ll get something done faster, but that feature will be public for everyone.\n\nif your server is big enough, i might do a unique spin off that uses the same backend as /reg/nal, but with a different name and icon, just shoot me a dm from the [development server](<https://discord.gg/4mteVXBDW7>)\n\nanywho, no need to donate, it just helps me uh, work on stuff more often, i guess.',
			color=await self.client.helpers.embed_color(ctx))
		embed.set_author(name='donation',icon_url='https://cdn.tyrant.link/blurple_tyrantlink.png')
		embed.add_field(name='github sponsors',value='https://github.com/sponsors/tyrantlink',inline=False)
		embed.add_field(name='monero (XMR)',value='`899YLWhurE1d4rMnNEbLUChXvRtQ6uiwbUCwEcy9gdSaDgJkHE5EWQPT31YKrATtcoRVUa1regt4mKLhhEhi38Kh1WjVNuz`',inline=False)
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.helpers.ephemeral(ctx))
	
	@slash_command(
		name='stats',
		description='get /reg/nal\'s session stats')
	async def slash_stats(self,ctx:ApplicationContext) -> None:
		raise NotImplementedError()