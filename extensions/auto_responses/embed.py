from utils.db.documents.ext.enums import AutoResponseType
from utils.db.documents import AutoResponse
from typing import TYPE_CHECKING
from discord import Embed

if TYPE_CHECKING:
    from client import Client


auto_response_404 = Embed(
    title='auto response not found!',
    color=0xff6969
)


def _normal_embed(
    auto_response: AutoResponse,
    client: 'Client',
    embed_color: int,
    include_statistics: bool = True
) -> Embed:
    embed = Embed(
        title=f'auto response {auto_response.id}',
        color=embed_color
    )

    embed.add_field(
        name='trigger', inline=True,
        value=f'`{auto_response.trigger}`'
    )

    embed.add_field(
        name='response type', inline=True,
        value=auto_response.type.name
    )

    embed.add_field(
        name='response', inline=False,
        value=auto_response.response
    )

    embed.add_field(
        name='source', inline=False,
        value=(
            client.helpers.handle_cmd_ref(auto_response.data.source)
            if auto_response.data.source else
            None
        )
    )

    embed.add_field(
        name='custom', inline=True,
        value=f'yes' if auto_response.data.custom else 'no'
    )

    embed.add_field(
        name='nsfw', inline=True,
        value='yes' if auto_response.data.nsfw else 'no'
    )

    for followup in auto_response.data.followups:
        embed.add_field(
            name=f'followup {auto_response.data.followups.index(followup)+1}',
            inline=False,
            value=f'`{followup.response}`'
        )

    if include_statistics:
        embed.set_footer(
            text=f'trigger count: {auto_response.statistics.trigger_count:,}'
        )

    return embed


async def _extra_embed(
    auto_response: AutoResponse,
    client: 'Client',
    embed_color: int,
    include_statistics: bool = True
) -> Embed:
    embed = Embed(
        title=f'auto response {auto_response.id}',
        color=embed_color
    )

    guild = await client.db.guild(auto_response.data.guild) if auto_response.data.guild else None

    au_data_type = 'unset'

    if auto_response.id != 'unset':
        match auto_response.id[0]:
            case 'b': au_data_type = 'base'
            case 'c': au_data_type = f'custom ({guild.name})'
            case 'u': au_data_type = f'unique ({guild.name})'
            case 'm': au_data_type = f'mention (<@{auto_response.trigger}>)'
            case 'p': au_data_type = f'personal (<@{auto_response.data.user}>)'
            case 's': au_data_type = f'[script](<https://github.com/tyrantlink/auto_response_dev>)'
            case  _: au_data_type = 'unknown'

    embed.add_field(
        name='data type', inline=False,
        value=au_data_type
    )

    embed.add_field(
        name='trigger', inline=True,
        value=f'`{auto_response.trigger}`'
    )

    embed.add_field(
        name='method', inline=True,
        value=auto_response.method.name
    )

    embed.add_field(
        name='response type', inline=True,
        value=auto_response.type.name
    )

    embed.add_field(
        name='response', inline=False,
        value=auto_response.response
    )

    embed.add_field(
        name='source', inline=False,
        value=(
            client.helpers.handle_cmd_ref(auto_response.data.source)
            if auto_response.data.source else
            None
        )
    )

    embed.add_field(
        name='weight', inline=True,
        value=auto_response.data.weight
    )

    embed.add_field(
        name='chance', inline=True,
        value=f'{auto_response.data.chance:.5g}%'
    )

    embed.add_field(
        name='ignore cooldown', inline=True,
        value=auto_response.data.ignore_cooldown
    )

    embed.add_field(
        name='regex matching', inline=True,
        value=auto_response.data.regex
    )

    embed.add_field(
        name='nsfw', inline=True,
        value=auto_response.data.nsfw
    )

    embed.add_field(
        name='case sensitive', inline=True,
        value=auto_response.data.case_sensitive
    )

    embed.add_field(
        name='delete trigger', inline=True,
        value=auto_response.data.delete_trigger
    )

    embed.add_field(
        name='user', inline=True,
        value=auto_response.data.user
    )

    embed.add_field(
        name='guild', inline=True,
        value=auto_response.data.guild
    )

    for index, followup in enumerate(auto_response.data.followups):
        embed.add_field(
            name=f'followup {index+1}', inline=False,
            value=f'`{followup.response}`'
        )

    if include_statistics:
        embed.set_footer(
            text=f'trigger count: {auto_response.statistics.trigger_count:,}'
        )

    return embed


async def au_info_embed(
    auto_response: AutoResponse,
    client: 'Client',
    embed_color: int,
    extra_info: bool = False,
    include_statistics: bool = True
) -> Embed:
    if auto_response.type == AutoResponseType.deleted:
        return Embed(
            title='this auto response has been deleted',
            color=0xff6969
        )

    return (
        await _extra_embed(
            auto_response,
            client,
            embed_color,
            include_statistics
        )
        if extra_info else
        _normal_embed(
            auto_response,
            client,
            embed_color,
            include_statistics
        )
    )
