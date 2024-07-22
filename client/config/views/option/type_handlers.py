from utils.db.documents.ext.enums import TWBFMode
from discord import ButtonStyle, SelectOption
from client.config.models import OptionType
from .typehint import ConfigOptionTypeHint


class ConfigOptionTypeHandler(ConfigOptionTypeHint):
    async def handle_option(self) -> None:
        self.clear_items()
        self.add_item(self.back_button)
        self.add_item(self.button_reset)

        match self.option.type:
            case OptionType.BOOL: await self.handle_bool()
            case OptionType.TWBF: await self.handle_twbf()
            case OptionType.STRING: await self.handle_string()
            case OptionType.INT: await self.handle_int()
            case OptionType.FLOAT: await self.handle_float()
            case OptionType.CHANNEL: await self.handle_channel()
            case OptionType.ROLE: await self.handle_role()
            case OptionType.USER: await self.handle_user()
            case _: raise ValueError('improper option type')

    async def handle_bool(self) -> None:
        self.add_item(self.button_true)
        self.add_item(self.button_false)

        self.get_item('button_true').style = (
            ButtonStyle.green
            if self.current_value() else
            ButtonStyle.red
        )

        self.get_item('button_false').style = (
            ButtonStyle.green
            if not self.current_value() else
            ButtonStyle.red
        )

    async def handle_twbf(self) -> None:
        self.add_item(self.button_true)
        self.add_item(self.button_whitelist)
        self.add_item(self.button_blacklist)
        self.add_item(self.button_false)

        self.get_item('button_true').style = ButtonStyle.blurple
        self.get_item('button_whitelist').style = ButtonStyle.blurple
        self.get_item('button_blacklist').style = ButtonStyle.blurple
        self.get_item('button_false').style = ButtonStyle.blurple

        match self.current_value():
            case TWBFMode.true: self.get_item('button_true').style = ButtonStyle.green
            case TWBFMode.whitelist: self.get_item('button_whitelist').style = ButtonStyle.green
            case TWBFMode.blacklist: self.get_item('button_blacklist').style = ButtonStyle.green
            case TWBFMode.false: self.get_item('button_false').style = ButtonStyle.green
            case _: raise ValueError('improper twbf mode')

        if self.current_value() in {TWBFMode.whitelist, TWBFMode.blacklist}:
            self.add_item(self.button_configure_channels)
            self.get_item(
                'button_configure_channels').label = f'configure {self.current_value().name}'

    async def handle_string(self) -> None:
        if not self.option.attrs.options:
            self.add_item(self.button_set)
            return

        self.add_item(self.select_string)

        self.get_item('select_string').options = [
            SelectOption(
                label=option.label,
                description=option.description,
                value=option.value)
            for option in
            self.option.attrs.options
        ]

    async def handle_int(self) -> None:
        self.add_item(self.button_set)

    async def handle_float(self) -> None:
        self.add_item(self.button_set)

    async def _handle_mentionable(self, mode: str, multi: bool) -> None:
        self.add_item(getattr(self, f'select_{mode}'))

        if self.option.attrs.max_value:
            self.get_item(
                f'select_{mode}').max_values = self.option.attrs.max_value

        if self.option.attrs.min_value:
            self.get_item(
                f'select_{mode}').min_values = self.option.attrs.min_value

        if multi:
            self.add_items(self.button_add, self.button_remove)

    async def handle_channel(self) -> None:
        await self._handle_mentionable('channel', self.option.attrs.multi)

    async def handle_role(self) -> None:
        await self._handle_mentionable('role', self.option.attrs.multi)

    async def handle_user(self) -> None:
        await self._handle_mentionable('user', self.option.attrs.multi)
