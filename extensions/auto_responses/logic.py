from discord.errors import Forbidden,NotFound,HTTPException
from utils.db.documents.ext.enums import AutoResponseType
from utils.pycord_classes import SubCog
from asyncio import create_task,sleep
from .classes import ArgParser
from discord import Message


class ExtensionAutoResponsesLogic(SubCog):
	async def cooldown(self,id:int,time:int) -> None:
		self._cooldowns.add(id)
		await sleep(time)
		self._cooldowns.remove(id)

	async def auto_response_handler(self,message:Message,args:ArgParser) -> None:
		# grab guild and user
		guild = await self.client.db.guild(message.guild.id)
		user = await self.client.db.user(message.author.id)
		# find matching response
		au = await self.client.au.get_response(
			message = message,
			args = args,
			overrides = guild.data.auto_responses.overrides,
			cross_guild = guild.config.auto_responses.allow_cross_guild_responses)
		# if no response found, return
		if au is None: return
		# format response based on type
		followups = au.data.followups
		match au.type:
			case AutoResponseType.text: response = au.response
			case AutoResponseType.file:
				response = await self.client.api.create_masked_au_url(au.id)
			case AutoResponseType.script: response,followups = await self.client.au.execute_au(au.id,message)
			case _: return
		# send response
		response_message = await message.channel.send(response)
		# delete original message if --delete was passed
		if args.delete:
			try: await message.delete()
			except (Forbidden,NotFound,HTTPException) as e:
				self.client.log.error(f'failed to delete message by {message.author.name} in {message.guild.name}',
					guild_id=message.guild.id,metadata={'au_id':au.id,'original_deleted':args.delete,'error':str(e)})
		# create message log
		await self.client.db.new.log(
			id=response_message.id,
			data={
				'au':au.id,
				'triggerer':message.author.id}
		).save()
		# create console log
		self.client.log.info(f'auto response {au.id} triggered by {message.author.name} in {message.guild.name}',
			guild_id=message.guild.id,metadata={'au_id':au.id,'original_deleted':args.delete})
		# add cooldown
		create_task(self.cooldown(message.author.id,guild.config.auto_responses.cooldown))
		# add to user found if no arguments were passed
		if not args and au.id not in user.data.auto_responses.found:
			user.data.auto_responses.found.append(au.id)
			await user.save_changes()
		# send followups
		for followup in followups:
			async with message.channel.typing():
				await sleep(followup.delay)
				await message.channel.send(followup.response)