from client.config.errors import ConfigValidationError
from utils.db.documents.ext.enums import TWBFMode
from .typehint import ConfigOptionTypeHint
from discord import User, Member, Role
from discord.abc import GuildChannel
from re import match, IGNORECASE


class ConfigOptionTypeValidator(ConfigOptionTypeHint):
    async def validate_bool(self, value: bool) -> bool:
        return value

    async def validate_twbf(self, value: TWBFMode) -> TWBFMode:
        return value

    async def validate_string(self, value: str) -> str:
        if (
            self.option.attrs.regex and
            not match(self.option.attrs.regex, value, IGNORECASE)
        ):
            raise ConfigValidationError(
                f'failed to match regex `{self.option.attrs.regex}`')

        if (
            self.option.attrs.options and
            self.option.attrs.enum is not None
        ):
            try:
                value = self.option.attrs.enum[value]
            except KeyError:
                raise ConfigValidationError(f'invalid option `{value}`')

        return value

    async def validate_int(self, value: str) -> int:
        try:
            value = int(value)
        except ValueError:
            raise ConfigValidationError('value must be an int')

        if (
            self.option.attrs.max_value and
            value > self.option.attrs.max_value
        ):
            raise ConfigValidationError(
                f'value cannot be greater than `{self.option.attrs.max_value}`')

        if (
            self.option.attrs.min_value and
            value < self.option.attrs.min_value
        ):
            raise ConfigValidationError(
                f'value cannot be less than `{self.option.attrs.min_value}`')

        return value

    async def validate_float(self, value: str) -> float:
        try:
            value = float(value)
        except ValueError:
            raise ConfigValidationError('value must be a float')

        if (
            self.option.attrs.max_value and
            value > self.option.attrs.max_value
        ):
            raise ConfigValidationError(
                f'value cannot be greater than `{self.option.attrs.max_value}`')

        if (
            self.option.attrs.min_value and
            value < self.option.attrs.min_value
        ):
            raise ConfigValidationError(
                f'value cannot be less than `{self.option.attrs.min_value}`')

        return value

    async def _validate_mentionable(
        self,
        value: GuildChannel | Role | User | Member
    ) -> GuildChannel | Role | User | Member:
        return value

    async def validate_channel(self, value: GuildChannel) -> GuildChannel:
        return await self._validate_mentionable(value)

    async def validate_role(self, value: Role) -> Role:
        return await self._validate_mentionable(value)

    async def validate_user(self, value: Member) -> User | Member:
        return await self._validate_mentionable(value)
