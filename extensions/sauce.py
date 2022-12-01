from discord.commands import Option as option,slash_command,message_command
from discord import Embed,ApplicationContext,Message,Guild
from aiofiles import open as aio_open
from os import environ,devnull,remove
environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # needs to be before nsfw_detector import
from discord.ext.commands import Cog
from aiohttp import ClientSession
from nsfw_detector import predict
from urllib.parse import quote
from secrets import token_hex
from main import client_cls
from asyncio import sleep
import sys


class art_services:
	def __init__(self) -> None:
		self.services = {
			'pixiv_id':'pixiv',
			'danbooru_id':'danbooru',
			'gelbooru_id':'gelbooru',
			'da_id':'deviantart',
			'fa_id':'furaffinity',
			'tweet_id':'twitter',
			'jp_name':'nhentai'}

	def determine_service(self,data:list) -> str|None:
		for trigger,service in self.services.items():
			if trigger in data: return service
		return None

	def get_embed_data(self,service:str,data:dict,header:dict) -> Embed|bool:
		match service:
			case 'pixiv': return (
				f'[{data.get("member_name",None)}](<https://www.pixiv.net/en/users/{quote(str(data.get("member_id",None)))}>)',
				f'[pixiv](<https://www.pixiv.net/en/artworks/{quote(str(data.get("pixiv_id",None)))}>)')
			case 'danbooru': return (
				f'[{data.get("creator",None)}](<https://danbooru.donmai.us/posts?tags={quote(str(data.get("creator",None)).replace(" ","_"))}&z=1>)',
				f'[danbooru](<https://danbooru.donmai.us/post/show/{quote(str(data.get("danbooru_id",None)))}>)')
			case 'gelbooru': return (
				f'[{data.get("creator",None)}](<https://gelbooru.com/index.php?page=post&s=list&tags={quote(str(data.get("creator",None)).replace(" ","_"))}>)',
				f'[gelbooru](<https://gelbooru.com/index.php?page=post&s=view&id={quote(str(data.get("gelbooru_id",None)))}>)')
			case 'deviantart': return (
				f'[{data.get("author_name",None)}](<{quote(str(data.get("author_url",None)))}>)',
				f'[deviantart](<https://deviantart.com/view/{quote(str(data.get("da_id",None)))}>)')
			case 'furaffinity': return (
				f'[{data.get("author_name",None)}](<{quote(str(data.get("author_url",None)))}>)',
				f'[furaffinity](<https://www.furaffinity.net/view/{quote(str(data.get("fa_id",None)))}>)')
			case 'twitter': return (
				f'[@{data.get("twitter_user_handle",None)}](<https://twitter.com/i/user/{quote(str(data.get("twitter_user_id",None)))}>)',
				f'[twitter](<https://twitter.com/i/web/status/{quote(str(data.get("tweet_id",None)))}>)')
			case 'nhentai': return (
				f'[{data.get("creator",[None])[0]}](<https://nhentai.net/artist/{quote(str(data.get("creator",["None"])[0].replace(" ","-")))}>)',
				f'[nhentai](<https://nhentai.net/g/{quote(str(header.get("thumbnail","None").split("%")[0].split("/")[-1]))}>)')
			case _: return False

class sauce_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client
		predict.tf.get_logger().setLevel(50)
		predict.tf.autograph.set_verbosity(0)
		self.nsfw_model = predict.load_model('nsfw_model')
		self.valid_formats = ['gif','jpg','png','bmp','webp']
		self.art = art_services()
		self.stdout = sys.stdout # save stdout 

		self.invalid_embed = Embed(title='ERROR',description='no valid images were found',color=0xff6969)
		self.invalid_embed.add_field(name='valid image types',value=", ".join(self.valid_formats))

		self.no_result_embed = Embed(title='failed to find a result',description='uhhhhh, good luck',color=0xff6969)

	async def _is_nsfw(self,url:str) -> bool:
		filepath = f'./tmp/nsfw_filter/{token_hex(8)}.{url.split(".")[-1]}'
		async with ClientSession() as session:
			async with session.get(url) as res:
				if res.status != 200: return None
				async with aio_open(filepath,'wb') as file:
					await file.write(await res.read())

		with open(devnull,'w') as null:
			sys.stdout = null # overwrite stdout
			out = predict.classify(self.nsfw_model,filepath)
			sys.stdout = self.stdout # return stdout
			remove(filepath)

		for k,v in out[list(out.keys())[0]].items():
			match k:
				case 'hentai' if v > 0.125: return True
				case 'porn'   if v > 0.18: return True
				case 'sexy'   if v > 0.60: return True
				case _: pass
		return False

	async def _api_key(self,guild:Guild) -> str:
		return await self.client.db.guilds.read(guild.id,['data','saucenao_key']) or self.client.env.saucenao_key	

	def _params(self,api_key:str,url:str) -> dict:
		return {
			'api_key':api_key,
			'output_type':2,
			'testmode':1,
			'numres':16,
			'hide':3,
			'dbmask':1657874285152,
			'url':url}

	async def _to_embed(self,image_url:str,result:dict,color:int,nsfw_allowed:bool,footer_text:str) -> Embed|bool:
		header = result.get('header',None)
		data   = result.get('data',None)
		if None in (header,data): return False
		confidence = float(header.get('similarity','0.0'))
		if confidence < 80: return False
		service = self.art.determine_service(data.keys())
		if service is None: return False
		if not nsfw_allowed:
			if service == 'nhentai' or await self._is_nsfw(image_url):
				return Embed(title='!!NSFW!!',description='the result may be nsfw, please run this command in an nsfw channel.',color=0xff6969)
		
		embed = Embed(title=data.get('eng_name',None) or data.get('jp_name',None) or data.get('title','no title'),color=color)
		fields = self.art.get_embed_data(service,data,header)
		if fields is None: return False
		embed.add_field(name='artist',value=fields[0],inline=True)
		embed.add_field(name='source',value=fields[1],inline=True)
		embed.add_field(name='confidence',value=f'{confidence}%',inline=True)
		if confidence > 90: embed.set_thumbnail(url=header.get("thumbnail",None))
		embed.set_footer(text=footer_text)
		return embed

	async def _get_result(self,params:dict) -> dict:
		async with ClientSession() as session:
				async with session.get(f'https://saucenao.com/search.php',params=params) as res:
					return await res.json()
	
	async def _base_sauce(self,ctx:ApplicationContext,message:Message) -> None:
		if len(message.attachments) == 0 and len(message.embeds) == 0:
			await ctx.response.send_message('this message has no attachments or embeds.',ephemeral=await self.client.hide(ctx))
			return
		valid = [
			a.url for a in message.attachments if a.filename.split('.')[-1] in self.valid_formats]+[
			e.image.url for e in [i for i in message.embeds if i.image] if e.image.url.split('.')[-1] in self.valid_formats]+[
			e.thumbnail.url for e in [i for i in message.embeds if i.thumbnail] if e.thumbnail.url.split('.')[-1] in self.valid_formats]
		if len(valid) == 0:
			await ctx.response.send_message(embed=self.invalid_embed,ephemeral=await self.client.hide(ctx))
			return
		await ctx.response.defer(ephemeral=await self.client.hide(ctx))
		results = []
		for url in valid:
			for i in range(3):
				result = await self._get_result(self._params(await self._api_key(ctx.guild),url))
				match result.get('header',{}).get('status',0):
					case 0: break # success
					case -2: # limited
						match result.get('header',{}).get('message','123456789')[8]:
							case 'D': # daily limit
								await ctx.followup.send(f'daily search limit exceeded.\nif a server moderator would like to increase this limit, they can purchase their own sauce nao api key here: https://saucenao.com/user.php?page=account-upgrades',ephemeral=await self.client.hide(ctx))
								return
							case 'S': # short limit
								await sleep(30)
								continue
							case '9': # no message given
								await ctx.followup.send(embed=self.no_result_embed,ephemeral=await self.client.hide(ctx))
								return
							case _: # unknown message given
								raise f'unknown saucenao error message: {result.get("header",{}).get("message","12345678")}'
					case _:
						await ctx.followup.send(embed=self.no_result_embed,ephemeral=await self.client.hide(ctx))
						return
			else:
				await ctx.followup.send(embed=self.no_result_embed,ephemeral=await self.client.hide(ctx))
				return
			embed = await self._to_embed(url,result.get('results',[{}])[0],await self.client.embed_color(ctx),ctx.channel.nsfw,
				f'30s limit: {result.get("header",{}).get("short_remaining",0)}/{result.get("header",{}).get("short_limit",0)} | 24h limit: {result.get("header",{}).get("long_remaining",0)}/{result.get("header",{}).get("long_limit",0)}')
			if embed: results.append(embed)
		if len(results) == 0:
			await ctx.followup.send(embed=self.no_result_embed,ephemeral=await self.client.hide(ctx))
			return
		await ctx.followup.send(embeds=results)

	@slash_command(
		name='sauce',
		description='image sauce | use the right click message command',
		guild_only=True,
		options=[
			option(str,name='message_id',description='e.g. 844131394276163614')])
	async def slash_sauce(self,ctx:ApplicationContext,message_id:str) -> None:
		if message_id.isnumeric(): # input is a message id
			message = self.client.get_message(int(message_id)) or await ctx.channel.fetch_message(int(message_id))
			if isinstance(message,Message):
				await self._base_sauce(ctx,message)
			else:
				await ctx.response.send_message('unable to access the message.\ncheck your input or try again by running the command in the channel the message was sent\nor just use the much better message command by right clicking (holding on mobile) a message, clicking apps, then clicking sauce',ephemeral=await self.client.hide(ctx))

	@message_command(name='sauce?')
	async def message_sauce(self,ctx:ApplicationContext,message:Message) -> None:
		await self._base_sauce(ctx,message)

def setup(client) -> None: client.add_cog(sauce_cog(client))