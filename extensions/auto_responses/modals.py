from discord import Member,Interaction
from discord.ui import Modal,InputText
from .shared import reload_guilds
from main import client_cls


class auto_response_modal(Modal):
	def __init__(self,client:client_cls,guild_id:int,title:str,items:list[InputText],method:str,user:Member=None,regex:bool=False,nsfw:bool=False) -> None:
		self.client   = client
		self.guild_id = guild_id
		self.method   = method
		self.user     = user
		self.regex    = regex
		self.nsfw     = nsfw
		super().__init__(title=title)
		for i in items: self.add_item(i)

	async def callback(self,interaction:Interaction) -> None:
		custom = await self.client.db.guilds.read(self.guild_id,['au','custom',self.method])
		trigger = (self.children[0].value if self.method == 'exact-cs' else self.children[0].value.lower()).strip()
		match len(self.children):
			case 1: # means is delete
				if trigger not in custom.keys():
					await interaction.response.send_message(f'> {trigger}\nnot found in custom auto responses!',ephemeral=True)
					return
				await self.client.db.guilds.unset(self.guild_id,['au','custom',self.method,trigger])
				await interaction.response.send_message(f'> {trigger}\nsuccessfully removed from auto responses',ephemeral=True)
			case 2: # means is add
				if trigger in custom.keys():
					await interaction.response.send_message(f'> {trigger}\nis already in the auto responses:',ephemeral=True)
					return
				au = {'response':self.children[1].value}
				if self.user is not None: au.update({'user':str(self.user.id)})
				if self.regex: au.update({'regex':True})
				if self.nsfw : au.update({'nsfw':True})
				await self.client.db.guilds.write(self.guild_id,['au','custom',self.method,trigger],au)
				await interaction.response.send_message(f'> {trigger}\nsuccessfully added to auto responses',ephemeral=await self.client.hide(interaction))
			case _: raise
		reload_guilds.append(self.guild_id)