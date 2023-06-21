from discord.commands import SlashCommandGroup,Option as option,slash_command,user_command
from discord import Embed,User,SlashCommand,File
from utils.classes import ApplicationContext
from ._shared_vars import generate_options
from discord.ext.commands import Cog
from client import Client
from random import choice
from io import StringIO
from json import dumps

NEWLINE = '\n'

class commands_commands(Cog):
	def __init__(self,client:Client) -> None:
		self.client = client

	profile = SlashCommandGroup('profile','get profile of a user or server')
	leaderboard = SlashCommandGroup('leaderboard','see various leaderboards')

	def identify_found_responses(self,found:list[str],guild_id:str=None) -> dict[str,int]:
		output = {'b':0,'ba':0,'g':0,'ga':0,'u':0,'ua':0,'p':0,'pa':0}
		for type,id,alt in (i.split(':') for i in found):
			if type[0] in ['g','u'] and type[1:] != guild_id: continue
			output[f'{type[0]}{"a" if int(alt) else ""}'] += 1
		return output

	async def base_profile_user(self,user:User,ctx:ApplicationContext) -> Embed:
		embed = Embed(
			title=f'{user.name}\'s profile',
			description=f"""id: {user.id}
			username: {user.name}
			discriminator: {user.discriminator}""".replace('	',''),
			color=await self.client.embed_color(ctx))
		embed.set_thumbnail(url=user.display_avatar.with_size(512).with_format('png').url)
		user_doc = await self.client.db.user(user.id).read()
		found_data = self.identify_found_responses(user_doc.get('data',{}).get('au',[]),str(ctx.guild_id))
		base_au = self.client.au.find({'custom':False,'user':None,'guild':None})
		description = f"""creation date: {user.created_at.strftime("%m/%d/%Y %H:%M:%S")}
			display name: {user.display_name}
			seen messages: {user_doc.get('messages',0)}"""
		embed.add_field(name='information:',value=description.replace('	',''),inline=False)
		embed.add_field(name='auto responses found:',value=f'base: {found_data.pop("b")}/{len(base_au)}\nalt : {found_data.pop("ba")}/{len([r for au in base_au for r in au.alt_responses])}',inline=False)
		if ctx.guild_id:
			if custom_au:=self.client.au.find({'custom':True,'user':None,'guild':str(ctx.guild_id)}):
				embed.add_field(name=f'custom responses found ({ctx.guild.name}):',value=f"""{f'base: {found_data["g"]}/{len(custom_au)}'}{NEWLINE if found_data['g'] and found_data['ga'] else ''}{f'alt : {found_data["ga"]}/{len([r for au in custom_au for r in au.alt_responses])}' if found_data['ga'] else ''}""",inline=False)
			if unique_au:=self.client.au.find({'custom':False,'user':None,'guild':str(ctx.guild_id)}):
				embed.add_field(name=f'unique responses found ({ctx.guild.name}):',value=f"""{f'base: {found_data["u"]}/{len(unique_au)}'}{NEWLINE if found_data['u'] and found_data['ua'] else ''}{f'alt : {found_data["ua"]}/{len([r for au in unique_au for r in au.alt_responses])}' if found_data['ua'] else ''}""",inline=False)
		if personal_au:=self.client.au.find({'custom':False,'user':str(user.id),'guild':None}):
			embed.add_field(name='personal responses found:',value=f"""{f'base: {found_data["p"]}/{len(personal_au)}' if found_data['p'] else ''}{NEWLINE if found_data['p'] and found_data['pa'] else ''}{f'alt : {found_data["pa"]}/{len([r for au in personal_au for r in au.alt_responses])}' if found_data['pa'] else ''}""",inline=False)
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
		description='get the profile of the current guild',
		guild_only=True)
	async def slash_profile_guild(self,ctx:ApplicationContext) -> None:
		embed = Embed(
			title=f'{ctx.guild.name}\'s profile',
			description=f"""id: {ctx.guild.id}
			username: {ctx.guild.name}
			owner: <@!{ctx.guild.owner_id}>""",
			color=await self.client.embed_color(ctx))
		if ctx.guild.icon:
			embed.set_thumbnail(url=ctx.guild.icon.with_size(512).with_format('png').url)
		guild_data = await self.client.db.guild(ctx.guild.id).data.read()
		embed.add_field(
			name='information:',
			value=f"""creation date: {ctx.guild.created_at.strftime("%m/%d/%Y %H:%M:%S")}
			member count: {ctx.guild.member_count}
			channels: {len(ctx.guild.channels)}
			roles: {len(ctx.guild.roles)}
			tts usage: {guild_data.get('tts',{}).get('usage')}
			unique auto responses: {len(self.client.au.find({'custom':False,'guild':str(ctx.guild.id)}))}
			custom auto responses: {len(self.client.au.find({'custom':True,'guild':str(ctx.guild.id)}))}""".replace('	',''))
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='get_data',
		description='get all data that /reg/nal has on you')
	async def slash_get_data(self,ctx:ApplicationContext) -> None:
		data = dumps(await self.client.db.user(ctx.author.id).read(),indent=2)
		if len(data)+8 > 2000: await ctx.response.send_message(file=File(StringIO(data),f'user{ctx.author.id}.json'),ephemeral=True)
		else: await ctx.response.send_message(f'```\n{data}\n```',ephemeral=True)

	@slash_command(
		name='generate',
		description='generate a sentence',
		options=[
			option(str,name='type',description='type',choices=['insult','excuse'])])
	async def slash_generate_insult(self,ctx:ApplicationContext,type:str) -> None:
		result = ' '.join([choice(v) for v in generate_options.get(type,{}).values()])
		await ctx.response.send_message(result,ephemeral=await self.client.hide(ctx))
		ctx.output.update({'result':result})

	@leaderboard.command(
		name='messages',
		description='view the message leaderboard',
		guild_only=True)
	async def slash_leaderboard_messages(self,ctx:ApplicationContext) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		res = {key: value for key, value in sorted((await self.client.db.guild(ctx.guild.id).data.leaderboards.messages.read()).items(),key=lambda item: item[1],reverse=True)}.items()
		output,index,nl = [f'total: {sum([int(v) for k,v in res])}\n'],1,'\n'
		for id,count in res:
			line = f'{index}{("th" if 4<=index%100<=20 else {1:"st",2:"nd",3:"rd"}.get(index%10, "th"))} - '
			line += f'{await self.client.db.user(int(id) if id.isnumeric() else id,).username.read()}: {count}'
			index += 1
			if len(f'{nl.join(output)}\n{line}') > 1980: break
			output.append(line)

		await ctx.followup.send(
			embed=Embed(
				title='Message Leaderboard:',
				description=nl.join(output),
				color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	@leaderboard.command(
		name='sticks',
		description='show talking stick leaderboard',
		guild_only=True)
	async def slash_leaderboard_sticks(self,ctx:ApplicationContext) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		res = {key: value for key, value in sorted((await self.client.db.guild(ctx.guild.id).data.leaderboards.sticks.read()).items(),key=lambda item: item[1],reverse=True)}.items()
		output,index,nl = [f'total: {sum([int(v) for k,v in res])}\n'],1,'\n'
		for id,count in res:
			line = f'{index}{("th" if 4<=index%100<=20 else {1:"st",2:"nd",3:"rd"}.get(index%10, "th"))} - '
			line += f'{await self.client.db.user(int(id) if id.isnumeric() else id).username.read()}: {count}'
			index += 1
			if len(f'{nl.join(output)}\n{line}') > 1980: break
			output.append(line)

		await ctx.followup.send(
			embed=Embed(
				title='Talking Stick Leaderboard:',
				description=nl.join(output),
				color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='command_stats',
		description='command usage stats')
	async def slash_command_stats(self,ctx:ApplicationContext) -> None:
		stats = (await self.client.db.inf('/reg/nal').command_usage.read())
		usage = {f'</{cmd.qualified_name}:{cmd.qualified_id}>' if isinstance(cmd,SlashCommand) else cmd.qualified_name:count for cmd in self.client.walk_application_commands() if (count:=stats.get(cmd.qualified_name,None)) is not None}
		usage = {key: value for key, value in sorted(usage.items(),key=lambda item: item[1],reverse=True)}
		await ctx.response.send_message(embed=Embed(
			title='command usage:',
			description='\n'.join([f'{command}: {usage[command]}' for command in usage]),
			color=await self.client.embed_color(ctx)),
			ephemeral=await self.client.hide(ctx))

	@user_command(name='view profile')
	async def user_profile_user(self,ctx:ApplicationContext,user:User) -> None:
		await ctx.response.send_message(embed=await self.base_profile_user(user,ctx),ephemeral=await self.client.hide(ctx))

def setup(client:Client) -> None:
	from .commands import commands_commands

	client._extloaded()
	client.add_cog(commands_commands(client))