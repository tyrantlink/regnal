from client.config.errors import ConfigValidationError
from client.config.models import OptionType
from .typehint import ConfigOptionTypeHint
from discord import Embed, Interaction
from typing import Any


class ConfigOptionLogic(ConfigOptionTypeHint):
    def current_value(self) -> Any:
        return getattr(getattr(self.object_doc.config, self.config_subcategory.name), self.option.name)

    def _convert_to_mention(self, value: Any) -> str:
        if value not in {'None', None}:
            match self.option.type:
                case OptionType.CHANNEL: return f'<#{value}>'
                case OptionType.ROLE: return f'<@&{value}>'
                case OptionType.USER: return f'<@{value}>'

        return str(value)

    def current_value_printable(self) -> str:
        value = self.current_value()

        return (
            '\n'.join([self._convert_to_mention(i) for i in value]) or 'None'
            if self.option.attrs.multi else
            self._convert_to_mention(value))

    async def give_warning(self, interaction: Interaction, warning: str | None) -> None:
        if warning is None:
            return

        await interaction.followup.send(embed=Embed(
            title='warning!', color=0xffff69,
            description=warning), ephemeral=True)

    async def generate_embed(self) -> None:
        embed_color = int((await self.client.db.guild(self.user.guild.id)).config.general.embed_color, 16)
        self.master.embed_color = embed_color

        self.embed = Embed(
            title=f'{self.option.name}', color=self.master.embed_color)

        if self.option.description:
            self.embed.description = self.client.helpers.handle_cmd_ref(
                self.option.description)

        match self.config_category.name:
            case 'user':
                self.embed.set_author(
                    name=self.user.display_name,
                    icon_url=self.user.display_avatar.url)
            case 'guild':
                self.embed.set_author(
                    name=self.user.guild.name,
                    icon_url=(
                        self.user.guild.icon.url
                        if self.user.guild.icon else
                        self.user.guild.me.display_avatar.url
                    ))
            case _:
                raise ValueError('improper config category name')

        self.embed.add_field(name='current value',
                             value=self.current_value_printable(), inline=False)

        self.embed.set_footer(
            text=f'config.{self.config_category.name}.{self.config_subcategory.name}.{self.option.name}')

    async def create_log(
        self,
        old_value: Any,
        old_value_printable: str,
        channel_id: int
    ) -> None:
        if old_value == self.current_value():
            return

        channel = self.user.guild.get_channel(channel_id)
        if channel is None:
            return

        embed = Embed(
            title=f'config changed!',
            color=0xffff69)

        embed.set_author(
            name=self.user.display_name,
            icon_url=self.user.display_avatar.url)

        embed.add_field(
            name='old value',
            value=old_value_printable,
            inline=True)

        embed.add_field(
            name='new value',
            value=self.current_value_printable(),
            inline=True)

        if (
                self.config_subcategory.name == 'logging' and
                self.option.name in {
                    'enabled',
                    'channel',
                    'log_commands'} and
                not bool(self.current_value())
        ):
            embed.add_field(
                name='note',
                value='this value can affect printing this log, future config changes may not be logged',
                inline=False)

        embed.set_footer(
            text=f'config.{self.config_category.name}.{self.config_subcategory.name}.{self.option.name}')

        await channel.send(embed=embed)

    async def write_config(self, value: Any, interaction: Interaction) -> str | None:
        try:
            warning = None

            if value is not None:
                match self.option.type:
                    case OptionType.BOOL:
                        value = await self.validate_bool(value)
                    case OptionType.TWBF:
                        value = await self.validate_twbf(value)
                    case OptionType.STRING:
                        value = await self.validate_string(value)
                    case OptionType.INT:
                        value = await self.validate_int(value)
                    case OptionType.FLOAT:
                        value = await self.validate_float(value)
                    case OptionType.CHANNEL:
                        value = await self.validate_channel(value)
                    case OptionType.ROLE:
                        value = await self.validate_role(value)
                    case OptionType.USER:
                        value = await self.validate_user(value)
                    case _:
                        raise ValueError('improper option type')

                if self.option.attrs.validation is not None:
                    value, warning = await self.option.attrs.validation(self.client, self.option, value, self.user)

            elif not self.option.nullable:
                raise ConfigValidationError('value cannot be None')

        except ConfigValidationError as e:
            e.add_note('suppress')
            raise e

        if (
            self.option.type in {
                OptionType.CHANNEL,
                OptionType.ROLE,
                OptionType.USER
            } and
            not self.option.attrs.multi
        ):
            value = value.id if value else None

        old_value_raw = self.current_value()
        old_value_printable = self.current_value_printable()

        setattr(getattr(self.object_doc.config,
                self.config_subcategory.name), self.option.name, value)

        await self.object_doc.save_changes()

        match self.config_category.name:
            case 'user': print_id = self.user.id
            case 'guild': print_id = self.user.guild.id
            case _: raise ValueError('improper config category name')

        self.client.log.info(
            f'{self.user.name} set {self.config_category.name}[{print_id}].{self.config_subcategory.name}.{self.option.name} to {value}',
            user=self.user.id,
            guild=getattr(
                getattr(self.user, 'guild', None), 'id', None),
            option=f'{self.config_category.name}.{self.config_subcategory.name}.{self.option.name}',
            value=value
        )

        await self.generate_embed()
        await self.handle_option()

        await interaction.response.edit_message(embed=self.embed, view=self)
        await self.give_warning(interaction, warning)

        if (
            self.config_category.name == 'guild' and
            (
                self.object_doc.config.logging.enabled or
                f'{self.config_subcategory.name}.{self.option.name}' == 'logging.enabled'
            ) and
            (
                self.object_doc.config.logging.channel or
                f'{self.config_subcategory.name}.{self.option.name}' == 'logging.channel' and
                old_value_raw
            ) and
            (
                self.object_doc.config.logging.log_commands or
                f'{self.config_subcategory.name}.{self.option.name}' == 'logging.log_commands'
            )
        ):
            await self.create_log(
                old_value_raw,
                old_value_printable,
                self.object_doc.config.logging.channel or old_value_raw
            )
