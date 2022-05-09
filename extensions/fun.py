from discord import File,Embed,InviteTarget,Role,ApplicationContext
from discord.commands import Option as option,slash_command
from main import client_cls,activity_options
from discord.ext.commands import Cog
from utils.tyrantlib import has_perm
from aiohttp import ClientSession
from random import randint,choice
from datetime import datetime
from re import sub

class fun_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		self.client = client
	
	@slash_command(
		name='activity',
		description='invite an embedded application to voice channel',
		options=[
			option(str,name='activity',description='name of application',choices=activity_options)])
	@has_perm('create_instant_invite')
	@has_perm('start_embedded_activities')
	async def slash_activity(self,ctx:ApplicationContext,activity:str) -> None:
		if not ctx.author.voice: await ctx.response.send_message('you must be in a voice channel to use this command!',ephemeral=await self.client.hide(ctx))
		activity_id = await self.client.db.inf.read('/reg/nal',['activities',activity])

		try: cache = await self.client.db.guilds.read(0,['activity_cache',str(ctx.author.voice.channel.id)])
		except: cache = []

		if str(activity_id) in cache: await ctx.response.send_message(f'[click to open {activity} in {ctx.author.voice.channel.name}](<https://discord.gg/{cache[str(activity_id)]}>)',ephemeral=await self.client.hide(ctx))
		else:
			invite = await ctx.author.voice.channel.create_invite(target_type=InviteTarget.embedded_application,target_application_id=activity_id,reason=f'{activity} created for {ctx.author.voice.channel.name}')
			await self.client.db.guilds.write(ctx.guild.id,['activity_cache',str(ctx.author.voice.channel.id),str(activity_id)],invite.code)
			await ctx.response.send_message(f'[click to open {activity} in {ctx.author.voice.channel.name}](<https://discord.gg/{invite.code}>)',ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='activity_custom',
		description='invite an embedded application to voice channel',
		options=[
			option(str,name='activity_id',description='application id')])
	async def slash_custom_activity(self,ctx:ApplicationContext,activity_id:str):
		if not ctx.author.voice: await ctx.response.send_message('you must be in a voice channel to use this command!',ephemeral=await self.client.hide(ctx))
		try: cache = await self.client.db.guilds.read(0,['activity_cache',str(ctx.author.voice.channel.id)])
		except: cache = []
		if str(activity_id) in cache: await ctx.response.send_message(f'[click to open {activity_id} in {ctx.author.voice.channel.name}](<https://discord.gg/{cache[str(activity_id)]}>)',ephemeral=await self.client.hide(ctx))
		else:
			invite = await ctx.author.voice.channel.create_invite(target_type=InviteTarget.embedded_application,target_application_id=activity_id,reason=f'{activity_id} created for {ctx.author.voice.channel.name}')
			await self.client.db.guilds.write(ctx.guild.id,['activity_cache',str(ctx.author.voice.channel.id),str(activity_id)],invite.code)
			await ctx.response.send_message(f'[click to open {activity_id} in {ctx.author.voice.channel.name}](<https://discord.gg/{invite.code}>)',ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='hello',
		description='say hello to /reg/nal?')
	async def slash_hello(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(
			file=File('images/regnal.png' if randint(0,100) else 'images/erglud.png'),
			ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='roll',
		description='roll dice with standard roll format',
		options=[
			option(str,name='roll',description='standard roll format e.g. (2d6+1+2+1d6-2)')])
	async def slash_roll(self,ctx:ApplicationContext,roll:str) -> None:
		rolls,modifiers = [],0
		embed = Embed(
			title=f'roll: {roll}',
			color=await self.client.embed_color(ctx))

		roll = sub(r'[^0-9\+\-d]','',roll).split('+')
		for i in roll:
			if '-' in i and not i.startswith('-'):
				roll.remove(i)
				roll.append(i.split('-')[0])
				for e in i.split('-')[1:]:
					roll.append(f'-{e}')

		for i in roll:
			e = i.split('d')
			try: [int(r) for r in e]
			except:
				await ctx.response.send_message('no.',ephemeral=await self.client.hide(ctx))
				return
			match len(e):
				case 1:
					modifiers += int(e[0])
				case 2:
					if int(e[1]) < 1:
						await ctx.response.send_message('no.',ephemeral=await self.client.hide(ctx))
						return
					for f in range(int(e[0])):
						res = randint(1,int(e[1]))
						rolls.append(res)
				case _: await ctx.response.send_message('invalid input',ephemeral=await self.client.hide(ctx))
		if rolls: embed.add_field(name='rolls:',value=rolls,inline=False)
		if modifiers != 0: embed.add_field(name='modifiers:',value=f"{'+' if modifiers > 0 else ''}{modifiers}",inline=False)
		embed.add_field(name='result:',value=sum(rolls)+modifiers)
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))

	@slash_command(
		name='time',
		description='/reg/nal can tell time.')
	async def slash_time(self,ctx:ApplicationContext) -> None:
		await ctx.response.send_message(datetime.now().strftime("%H:%M:%S.%f"))

	@slash_command(
		name='poll',
		description='start a poll',
		options=[
			option(str,name='title',description='title of poll'),
			option(str,name='description',description='description of poll'),
			option(str,name='option_a',description='option a'),
			option(str,name='option_b',description='option b'),
			option(str,name='option_c',description='option c',required=False,default=None),
			option(str,name='option_d',description='option d',required=False,default=None),
			option(str,name='other',description='create thread of other answers and discussion',required=False,default=None)])
	@has_perm('manage_guild')
	async def slash_poll(self,ctx:ApplicationContext,title:str,description:str,option_a:str,option_b:str,option_c:str,option_d:str,other:str) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		reactions = ['🇦','🇧']
		response = f'{description}\n\n🇦: {option_a}\n🇧: {option_b}'

		for option,emote in [(option_c,'🇨'),(option_d,'🇩')]:
			response += f'\n{emote} {option}'
			reactions.append(emote)
		
		if other:
			response += f'\n🇴 other, specify in thread'
			reactions.append('🇴')
			
		message = await ctx.channel.send(embed=Embed(
			title=title,
			description=response))
		
		for reaction in reactions:
			await message.add_reaction(reaction)
		
		if other: message.create_thread(name=title)
	
	@slash_command(
		name='8ball',
		description='ask the 8ball a question',
		options=[
			option(str,name='question',description='question to ask')])
	async def slash_eightball(self,ctx:ApplicationContext,question:str) -> None:
		await ctx.response.send_message(choice(await self.client.db.inf.read('questions',['8ball'])))

	@slash_command(
		name='color',
		description='generate a random color')
	async def slash_color(self,ctx):
		color = hex(randint(0,16777215)).upper()
		res = [f'#{color[2:]}']
		res.append(f'R: {int(color[2:4],16)}')
		res.append(f'G: {int(color[4:6],16)}')
		res.append(f'B: {int(color[6:8],16)}')
		await ctx.response.send_message(
			embed=Embed(
				title='random color:',
				description=f"""#{color[2:]}

				R: {int(color[2:4],16)}
				G: {int(color[4:6],16)}
				B: {int(color[6:8],16)}""",
				color=int(color,16)),
			ephemeral=await self.client.hide(ctx))
	
	@slash_command(
		name='shorten',
		description='shorten a link with s.tyrant.link',
		options=[
			option(str,name='url',description='e.g. https://example.com'),
			option(str,name='name',description='name of link'),
			option(str,name='path',description='s.tyrant.link/{path}, randomized if left empty',required=None,default=None)])
	async def slash_shorten(self,ctx:ApplicationContext,url:str,name:str,path:str) -> None:
		# await ctx.defer(ephemeral=await self.client.hide(ctx))
		link_data = {
			"longUrl": url,
			"title": name,
			"shortCodeLength": 8,
			"tags": ["/reg/nal"]}
		if path: link_data.update({"customSlug":sub(' ','',path)})
		async with ClientSession() as session:
			async with session.post('https://s.tyrant.link/rest/v2/short-urls',json=link_data,headers={'X-Api-Key':self.client.env.shlink}) as res:
				out = await res.json()
				match res.status:
					case 200:
						await ctx.response.send_message(
							embed=Embed(
								title='your link has been shortened:',
								description=sub('http://','https://',out['shortUrl']),
								color=await self.client.embed_color(ctx)),
							ephemeral=await self.client.hide(ctx))
					case 400:
						if out['detail'] == f'Provided slug "{path}" is already in use.':
							await ctx.response.send_message(f'path "{path}" is already in use',ephemeral=await self.client.hide(ctx))
						else:
							await ctx.response.send_message(f'unknown error, please submit issue with /issue\ndetails: {out["detail"]}',ephemeral=await self.client.hide(ctx))
							await self.client.log.error(f'[SHLINK] {out["detail"]}')
					case _: await ctx.response.send_message(f'unknown error, please submit issue with /issue\nstatus code: {res.status}',ephemeral=await self.client.hide(ctx))


	@slash_command(
		name='random',
		description='get random user with role',
		options=[
			option(Role,name='role',description='role to roll users from'),
			option(bool,name='ping',description='ping the result user? (requires mention_everyone)')])
	@has_perm('guild_only')
	async def slash_random(self,ctx:ApplicationContext,role:Role,ping:bool) -> None:
		if ping and not has_perm('mention_everyone',ctx): return
		result = choice(role.members)
		await ctx.response.send_message(f"{result.mention if ping else result} was chosen!",ephemeral=await self.client.hide(ctx))

	async def acquire_hentai(self) -> tuple:
		id = randint(1,400493)
		async with ClientSession() as session:
			async with session.get(f'https://nhentai.net/api/gallery/{id}') as res:
				match res.status:
					case 200: return (await res.json(),id)
					case _: return ({'error':'cock'},id)

	@slash_command(
		name='hentai',
		description='get a random nhentai doujin to read.')
	async def slash_hentai(self,ctx:ApplicationContext) -> None:
		await ctx.defer(ephemeral=await self.client.hide(ctx))
		for i in range(10):
			out,id = await self.acquire_hentai()
			if 'error' not in out.keys(): break
		else: await ctx.response.send_message(f'failed to acquire hentai, try again in like, five minutes',ephemeral=await self.client.hide(ctx))
	
		embed = Embed(
				title='random nhentai:',
				description=f'https://nhentai.net/g/{id}',
				color=await self.client.embed_color(ctx))
		img_url = f'https://t.nhentai.net/galleries/{out["media_id"]}/cover.'
		match out['images']['cover']['t']:
			case 'p': img_url += 'png'
			case 'j': img_url += 'jpg'
			case 'g': img_url += 'gif'
		embed.set_image(url=img_url)
		info = {'parodies':[],'characters':[],'tags':[],'artists':[],'groups':[],'languages':[],'pages':[str(len(out["images"]["pages"]))]}
		for i in out['tags']:
			match i['type']:
				case 'parody': info['parodies'].append(i['name'])
				case 'character': info['characters'].append(i['name'])
				case 'tag': info['tags'].append(i['name'])
				case 'artist': info['artists'].append(i['name'])
				case 'group': info['groups'].append(i['name'])
				case 'language': info['languages'].append(i['name'])
				case 'category': pass
				case _: print(f'unknown tag type `{i["type"]}`')
		for k,v in info.items():
			if v: embed.add_field(name=k,value=', '.join(v),inline=True)
		await ctx.response.send_message(embed=embed,ephemeral=await self.client.hide(ctx))


def setup(client:client_cls) -> None: client.add_cog(fun_cog(client))
