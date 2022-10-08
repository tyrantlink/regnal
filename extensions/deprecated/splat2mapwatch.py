from discord.commands import SlashCommandGroup
from discord import ApplicationContext
from utils.tyrantlib import perm
from discord.ext.commands import Cog
from discord.ext.tasks import loop
from aiohttp import ClientSession
from datetime import datetime
from main import client_cls
from time import time

class splat2mapwatch_cog(Cog):
	def __init__(self,client:client_cls) -> None:
		client._extloaded()
		self.client = client
		self.channel = None
		self.channel_id = 969251621844418580
		self.soon = []
		self.sent = []
		self.mapwatch_loop.start()
		self.soon_loop.start()
	
	splatoon = SlashCommandGroup('splatoon','splatoon 2 commands')

	@splatoon.command(
		name='restart_mapwatch',
		description='restart mapwatch loop')
	@perm('bot_owner')
	async def slash_splatoon_restart_mapwatch(self,ctx:ApplicationContext) -> None:
		self.mapwatch_loop.restart()
		await ctx.response.send_message('mapwatch loop restarted')

	@loop(hours=1)
	async def mapwatch_loop(self) -> None:
		async with ClientSession() as session:
			async with session.get('https://splatoon2.ink/data/schedules.json') as req:
				res,dm = await req.json(),[]
				for i in res['gachi']:
					if '19' in [i['stage_a']['id'],i['stage_b']['id']] and i['start_time'] not in self.sent:
						if self.channel is None: self.channel = await self.client.fetch_channel(self.channel_id)
						self.sent.append(i['start_time'])
						if self.soon == []: self.soon = [i['start_time'],14400,7200,3600,1800,900,300,0]
						day = int(datetime.fromtimestamp(i['start_time']).strftime(f"%d"))
						dm.append(f'hotel {i["rule"]["key"]} on {datetime.fromtimestamp(i["start_time"]).strftime(f"%B %d")}{("th" if 4<=day%100<=20 else {1:"st",2:"nd",3:"rd"}.get(day%10, "th"))} at {datetime.fromtimestamp(i["start_time"]).strftime(f"%H%M")}')
				if dm: await self.channel.send('\n'.join(dm))
		
	@loop(seconds=5)
	async def soon_loop(self) -> None:
		if self.soon == []: return
		if self.soon[0]-time() <= self.soon[1]:
			match self.soon[1]:
				case 0: dm = 'hotel has started, go play the video game.'
				case 300: dm = 'hotel in 5 minutes'
				case 900: dm = 'hotel in 15 minutes'
				case 1800: dm = 'hotel in 30 minutes'
				case 3600: dm = 'hotel in 1 hour'
				case 7200: dm = 'hotel in 2 hours'
				case 14400: dm = 'hotel in 4 hours'
				case _: return

			await self.channel.send(dm)
			self.soon.pop(1)
			if len(self.soon) == 1: self.soon = []





def setup(client) -> None:
	client.add_cog(splat2mapwatch_cog(client))