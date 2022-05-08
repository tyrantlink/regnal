from discord.commands import SlashCommandGroup,Option as option,slash_command,user_command
from discord import Embed,User,ApplicationContext
from discord.ext.commands import Cog
from utils.tyrantlib import has_perm
from main import client_cls
from random import choice
from json import dumps

class commands_cog(Cog):
	def __init__(self,client:client_cls):
		self.client = client

	profile = SlashCommandGroup('profile','get profile of a user or server')
	leaderboard = SlashCommandGroup('leaderboard','see various leaderboards')

	async def base_profile_user(self,user:User,ctx:ApplicationContext) -> Embed:
		embed = Embed(
			title=f'{user.name}\'s profile',
			description=f"""id: {user.id}
			username: {user.name}
			discriminator: {user.discriminator}""",
			color=await self.client.embed_color(ctx))
		embed.set_thumbnail(url=user.display_avatar.with_size(512).with_format('png').url)
		bday = await self.client.db.users.read(user.id,['birthday'])
		embed.add_field(
			name='information:',
			value=f"""creation date: {user.created_at.strftime("%m/%d/%Y %H:%M:%S")}
			display name: {user.display_name}
			birthday: {'not set' if not bday else 'hidden' if bday.startswith('h') else bday}
			seen messages: {await self.client.db.users.read(user.id,['messages'])}""")
		return embed

	@profile.command(
		name='user',
		description='get a user\'s profile',
		options=[
			option(User,name='user',description='user',required=False,default=None)])
	async def slash_profile_user(self,ctx:ApplicationContext,user:User) -> None:
		if not user: user = ctx.author
		await ctx.response.send_message(embed=await self.base_profile_user(user,ctx),ephemeral=await self.client.hide(ctx))

	@profile.command(
		name='guild',
		description='get the profile of the current guild')
	@has_perm('guild_only')
	async def slash_profile_guild(self,ctx:ApplicationContext) -> None:
		embed = Embed(
			title=f'{ctx.guild.name}\'s profile',
			description=f"""id: {ctx.guild.id}
			username: {ctx.guild.name}
			owner: <@!{ctx.guild.owner_id}>""",
			color=await self.client.embed_color(ctx))
		if ctx.guild.icon:
			embed.set_thumbnail(url=ctx.guild.icon.with_size(512).with_format('png').url)
		embed.add_field(
			name='information:',
			value=f"""creation date: {ctx.guild.created_at.strftime("%m/%d/%Y %H:%M:%S")}
			member count: {ctx.guild.member_count}
			channels: {len(ctx.guild.channels)}
			roles: {len(ctx.guild.roles)}""")
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='get_data',
		description='get all data that /reg/nal has on you')
	async def slash_get_data(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(f'```\n{dumps(await self.client.db.users.read(ctx.author.id),indent=2)}\n```',ephemeral=True)

	@slash_command(
		name='generate_insult',
		description='generate a random insult')
	async def slash_generate_insult(self,ctx:ApplicationContext) -> None:
		dictionary = await self.client.db.inf.read('dictionary')
		await ctx.response.send_message(f"{choice(dictionary['adjective'])} {choice(dictionary['noun'])}",ephemeral=await self.client.hide(ctx))
	
	@leaderboard.command(
		name='messages',
		description='view the message leaderboard')
	@has_perm('guild_only')
	async def slash_leaderboard_messages(self,ctx:ApplicationContext) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		output,index,nl = [],1,'\n'
		for id,count in {key: value for key, value in sorted((await self.client.db.guilds.read(ctx.guild.id,['leaderboards','messages'])).items(),key=lambda item: item[1],reverse=True)}.items():
			line = f'{index}{("th" if 4<=index%100<=20 else {1:"st",2:"nd",3:"rd"}.get(index%10, "th"))} - '
			line += f'{await self.client.db.users.read(int(id),["username"])}: {count}'
			index += 1
			if len(f'{nl.join(output)}\n{line}') > 1980: break
			output.append(line)

		await ctx.response.send_message(embed=Embed(title='Message Leaderboard:',description=nl.join(output),color=await self.client.embed_color(ctx)),ephemeral=await self.client.hide(ctx))

	@leaderboard.command(
		name='sticks',
		description='show talking stick leaderboard')
	async def slash_leaderboard_sticks(self,ctx:ApplicationContext) -> None:
		await self.check(ctx)
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		output,index,nl = [],1,'\n'
		for id,count in {key: value for key, value in sorted((await self.client.db.guilds.read(ctx.guild.id,['leaderboards','sticks'])).items(),key=lambda item: item[1],reverse=True)}.items():
			line = f'{index}{("th" if 4<=index%100<=20 else {1:"st",2:"nd",3:"rd"}.get(index%10, "th"))} - '
			line += f'{await self.client.db.users.read(int(id),["username"])}: {count}'
			index += 1
			if len(f'{nl.join(output)}\n{line}') > 1980: break
			output.append(line)

		await ctx.response.send_message(
			embed=Embed(
				title='Talking Stick Leaderboard:',
				description=nl.join(output),
				color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='command_stats',
		description='command usage stats')
	async def slash_command_stats(self,ctx:ApplicationContext) -> None:
		usage = {key: value for key, value in sorted((await self.client.db.inf.read('command_usage',['usage'])).items(),key=lambda item: item[1],reverse=True)}
		
		await ctx.response.send_message(embed=Embed(
			title='command usage:',
			description='\n'.join([f'{command}: {usage[command]}' for command in usage]),
			color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	@user_command(name='get profile')
	async def user_profile_user(self,ctx:ApplicationContext,user:User) -> None:
		await ctx.response.send_message(embed=await self.base_profile_user(user,ctx),ephemeral=await self.client.hide(ctx))


def setup(client:client_cls) -> None: client.add_cog(commands_cog(client))