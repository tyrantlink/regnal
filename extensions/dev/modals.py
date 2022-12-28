from discord import Embed,InputTextStyle,Interaction,ForumChannel
from discord.ui import InputText,Modal
from client import Client


class dev_modal(Modal):
	def __init__(self,client:Client,format:str) -> None:
		self.client = client
		self.format = format
		match format:
			case 'commit':
				super().__init__(title='make a commit')
				self.add_item(InputText(label='title',max_length=256,style=InputTextStyle.short))
				self.add_item(InputText(label='version_bump',max_length=5,placeholder='none,patch,minor,major',style=InputTextStyle.short))
				self.add_item(InputText(label='new_features',max_length=1024,required=False,style=InputTextStyle.long))
				self.add_item(InputText(label='fixes',max_length=1024,required=False,style=InputTextStyle.long))
				self.add_item(InputText(label='notes',max_length=1024,required=False,style=InputTextStyle.long))
			case 'issue':
				super().__init__(title='submit an issue')
				self.add_item(InputText(label='title',max_length=256,placeholder='title of issue',style=InputTextStyle.short))
				self.add_item(InputText(label='details',max_length=1024,placeholder='details of issues',style=InputTextStyle.long,required=False))
			case 'suggestion':
				super().__init__(title='submit a suggestion')
				self.add_item(InputText(label='title',max_length=256,placeholder='title of suggestion',style=InputTextStyle.short))
				self.add_item(InputText(label='details',max_length=1024,placeholder='details of suggestion',style=InputTextStyle.long,required=False))
			case _: raise

	def bump_version(self,current_version:str,bump_type:str) -> str:
		ma,mi,p = current_version.split('.')
		match bump_type:
			case 'major': ma,mi,p = str(int(ma)+1),'0','0'
			case 'minor': mi,p = str(int(mi)+1),'0'
			case 'patch': p = str(int(p)+1)
		return '.'.join([ma,mi,p])

	async def report(self,interaction:Interaction,type:str,title:str,details:str) -> None:
		channel:ForumChannel = await self.client.fetch_channel(await self.client.db.inf.read('/reg/nal',['development','support']))
		embed = Embed(title=title,description=details,color=await self.client.embed_color(interaction))
		embed.set_author(name=str(interaction.user),url=interaction.user.jump_url,icon_url=interaction.user.avatar.url)
		await channel.create_thread(name=title,embed=embed,
			applied_tags=[tag for tag in channel.available_tags if tag.name in [type,'open']])

	async def commit(self,interaction:Interaction,title:str,version_bump:str,new_features:str,fixes:str,notes:str) -> None:
		channel = await self.client.fetch_channel(await self.client.db.inf.read('/reg/nal',['development','change_log']))
		if version_bump != 'none':
			await self.client.db.inf.write('/reg/nal',['version'],self.bump_version(await self.client.db.inf.read('/reg/nal',['version']),version_bump))
		embed=Embed(title=f"v{await self.client.db.inf.read('/reg/nal',['version'])} | {title}",color=await self.client.embed_color(interaction))

		if new_features: embed.add_field(name='new features:',value=new_features,inline=False)
		if fixes: embed.add_field(name='bug fixes:',value=fixes,inline=False)
		if notes: embed.add_field(name='notes:',value=notes,inline=False)
		embed.add_field(
			name="please report bugs with /issue\ncommands may take up to an hour to update globally.",
			value='[development server](<https://discord.gg/4mteVXBDW7>)')
		embed.set_footer(text=f'version {await self.client.db.inf.read("/reg/nal",["version"])} ({self.client.commit_id})')
		message = await channel.send(embed=embed)
		await message.publish()

	async def callback(self,interaction:Interaction) -> None:
		match self.format:
			case 'commit': 
				await self.commit(interaction,self.children[0].value,self.children[1].value,self.children[2].value,self.children[3].value,self.children[4].value)
				await interaction.response.send_message('successfully announced commit',ephemeral=True)
			case 'issue'|'suggestion': 
				await self.report(interaction,self.format,self.children[0].value,self.children[1].value)
				embed = Embed(title=f'{self.format} reported',description='you can check for a resolution on the [development server](<https://discord.gg/4mteVXBDW7>)',color=await self.client.embed_color(interaction))
				await interaction.response.send_message(embed=embed,ephemeral=True)
			case _: raise ValueError('unknown modal format')