from client.config.models import ConfigCategory, ConfigSubcategory, ConfigOption
from discord import Interaction, User, Member, Role
from utils.db.documents.ext.enums import TWBFMode
from utils.pycord_classes import SubView
from discord.ui import button, select
from discord.abc import GuildChannel
from typing import Any


class ConfigOptionTypeHint(SubView):
    def __init__(self) -> None:
        self.config_category: ConfigCategory
        self.config_subcategory: ConfigSubcategory
        self.selected_options: set[str | int]
        self.option: ConfigOption
        self.user: User | Member

    def current_value(self) -> Any: ...
    def current_value_printable(self) -> str: ...
    async def give_warning(self, interaction: Interaction,
                           warning: str | None) -> None: ...

    async def generate_embed(self) -> None: ...
    async def write_config(self, value: Any) -> str | None: ...
    async def handle_option(self) -> None: ...
    async def handle_bool(self) -> None: ...
    async def handle_twbf(self) -> None: ...
    async def handle_string(self) -> None: ...
    async def handle_int(self) -> None: ...
    async def handle_float(self) -> None: ...
    async def handle_channel(self) -> None: ...
    async def handle_role(self) -> None: ...
    async def handle_user(self) -> None: ...
    async def validate_bool(self, value: bool) -> bool: ...
    async def validate_twbf(self, value: TWBFMode) -> TWBFMode: ...
    async def validate_string(self, value: str) -> str: ...
    async def validate_int(self, value: str) -> int: ...
    async def validate_float(self, value: str) -> float: ...
    async def validate_channel(self, value: GuildChannel) -> GuildChannel: ...
    async def validate_role(self, value: Role) -> Role: ...
    async def validate_user(self, value: Member) -> User | Member: ...

    async def button_reset(self, button: button,
                           interaction: Interaction) -> None: ...

    async def button_true(self, button: button,
                          interaction: Interaction) -> None: ...

    async def button_false(self, button: button,
                           interaction: Interaction) -> None: ...

    async def button_whitelist(
        self, button: button, interaction: Interaction) -> None: ...

    async def button_blacklist(
        self, button: button, interaction: Interaction) -> None: ...

    async def button_configure_channels(
        self, button: button, interaction: Interaction) -> None: ...

    async def button_set(self, button: button,
                         interaction: Interaction) -> None: ...

    async def button_add(self, button: button,
                         interaction: Interaction) -> None: ...

    async def button_remove(self, button: button,
                            interaction: Interaction) -> None: ...

    async def select_channel(self, select: select,
                             interaction: Interaction) -> None: ...

    async def select_role(self, select: select,
                          interaction: Interaction) -> None: ...

    async def select_user(self, select: select,
                          interaction: Interaction) -> None: ...

    async def select_string(self, select: select,
                            interaction: Interaction) -> None: ...
