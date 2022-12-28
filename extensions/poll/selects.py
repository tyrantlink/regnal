from discord import SelectOption,Interaction,Embed
from discord.ui import Select
from client import Client


class poll_published_select(Select):
	def __init__(self,client:Client,options:list[SelectOption]) -> None:
		self.client = client
		if options is None: options = range(25)
		super().__init__(
			placeholder='vote for an option',
			min_values=0,
			max_values=1,
			options=options,
			custom_id='test2')

	async def callback(self,interaction:Interaction) -> None:
		data:dict = await self.client.db.polls.read(interaction.message.id)
		if str(interaction.user.id) in data['voters'].keys():
			await self.client.db.polls.dec(interaction.message.id,['options',data['voters'][str(interaction.user.id)],'votes'])
			data['options'][data['voters'][str(interaction.user.id)]]['votes'] -= 1
		await self.client.db.polls.inc(interaction.message.id,['options',self.values[0],'votes'])
		data['options'][self.values[0]]['votes'] += 1
		await self.client.db.polls.write(interaction.message.id,['voters',str(interaction.user.id)],self.values[0])
		options = data['options']
		embed = Embed(title=data['embed']['title'],description=data['embed']['description'],color=data['embed']['color'])
		for k,v in options.items(): embed.add_field(name=f'{v["votes"]} | {k}',value=v['description'],inline=False)
		await interaction.response.edit_message(embed=embed)
		await self.client.log.debug('responded to interaction callback')