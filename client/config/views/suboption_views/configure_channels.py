from ...models import ConfigCategory,ConfigSubcategory,ConfigOption,OptionType
from utils.atomic_view import SubView,MasterView
from discord import User,Member,Embed,Button,ButtonStyle,Interaction
from discord.ui import button
from typing import Any
from utils.db.documents.ext.enums import TWBFMode


class ConfigChannelsView(SubView):
	...