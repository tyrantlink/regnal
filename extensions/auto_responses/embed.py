from utils.db.documents.ext.enums import AutoResponseMethod,AutoResponseType
if not 'TYPE_HINT': from client import Client
from utils.db.documents import AutoResponse
from discord import Embed


def _normal_embed(auto_response:AutoResponse,embed_color:int) -> Embed:
	embed = Embed(
		title=f'auto response {auto_response.id}',
		color=embed_color)
	embed.add_field(
		name='trigger',inline=True,
		value=f'`{auto_response.trigger}`')
	embed.add_field(
		name='response type',inline=True,
		value=auto_response.type.name)
	embed.add_field(
		name='response',inline=False,
		value=auto_response.response)
	embed.add_field(
		name='source',inline=False,
		value=auto_response.data.source)
	embed.add_field(
		name='custom',inline=True,
		value=f'yes' if auto_response.data.custom else 'no')
	embed.add_field(
		name='nsfw',inline=True,
		value='yes' if auto_response.data.nsfw else 'no')
	for followup in auto_response.data.followups:
		embed.add_field(
			name=f'followup {auto_response.data.followups.index(followup)+1}',inline=False,
			value=f'`{followup.response}`')
	return embed

def _extra_embed(auto_response:AutoResponse,embed_color:int) -> Embed:
	embed = Embed(
		title=f'auto response {auto_response.id}',
		color=embed_color)
	match auto_response.id[0]:
		case 'b': au_data_type = 'base'
		case 'c': au_data_type = f'custom ({auto_response.data.guild})'
		case 'u': au_data_type = f'unique ({auto_response.data.guild})'
		case 'm': au_data_type = f'mention ({auto_response.trigger})'
		case 'p': au_data_type = f'personal ({auto_response.data.user})'
		case 's': au_data_type = 'scripted'
		case  _ : au_data_type = 'unknown'
	embed.add_field(
		name='data type',inline=False,
		value=au_data_type)
	embed.add_field(
		name='trigger',inline=True,
		value=f'`{auto_response.trigger}`')
	embed.add_field(
		name='method',inline=True,
		value=auto_response.method.name)
	embed.add_field(
		name='response type',inline=True,
		value=auto_response.type.name)
	embed.add_field(
		name='response',inline=False,
		value=auto_response.response)
	embed.add_field(
		name='source',inline=False,
		value=auto_response.data.source)
	embed.add_field(
		name='weight',inline=True,
		value=auto_response.data.weight)
	embed.add_field(
		name='ignore cooldown',inline=True,
		value=auto_response.data.ignore_cooldown)
	embed.add_field(
		name='regex matching',inline=True,
		value=auto_response.data.regex)
	embed.add_field(
		name='nsfw',inline=True,
		value=auto_response.data.nsfw)
	embed.add_field(
		name='case sensitive',inline=True,
		value=auto_response.data.case_sensitive)
	embed.add_field(
		name='delete trigger',inline=True,
		value=auto_response.data.delete_trigger)
	embed.add_field(
		name='user',inline=True,
		value=auto_response.data.user)
	embed.add_field(
		name='guild',inline=True,
		value=auto_response.data.guild)
	for followup in auto_response.data.followups:
		embed.add_field(
			name=f'followup {auto_response.data.followups.index(followup)+1}',inline=False,
			value=f'`{followup.response}`')
	return embed


def au_info_embed(
	auto_response:AutoResponse,
	embed_color:int,
	extra_info:bool=False
) -> Embed:
	return _extra_embed(auto_response,embed_color) if extra_info else _normal_embed(auto_response,embed_color)