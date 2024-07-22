# imported here for client to import
from .base import register_permissions as register_base_permissions
from discord import Member, Guild
from typing import TYPE_CHECKING
from typing import Iterable
from re import match

if TYPE_CHECKING:
    from client import Client


class PermissionHandler:
    def __init__(self, client: 'Client') -> None:
        self.client = client
        self.permissions = set()
        register_base_permissions(self)

    def register_permission(self, permission: str) -> None:
        self.permissions.add(permission)
        self.client.log.debug(f'registered permission {permission}')

    def unregister_permission(self, permission: str) -> None:
        self.permissions.discard(permission)
        self.client.log.debug(f'unregistered permission {permission}')

    def matcher(self, pattern: str, check: Iterable[str] = None) -> set[str]:
        check = check if check is not None else self.permissions
        pattern = pattern.replace('.', '\.').replace('*', '.*')
        return set(filter(lambda p: match(f'^{pattern}$', p), check))

    async def user(self, user: Member, guild: Guild) -> set[str]:
        guild_patterns = (await self.client.db.guild(guild.id)).data.permissions
        user_roles = {
            str(r.id)
            for r in user.roles
            if str(r.id)
            in guild_patterns
        }

        if str(user.id) in guild_patterns:
            user_roles.add(str(user.id))

        is_dev = user.id in self.client.owner_ids and self.client.project.config.dev_bypass

        raw_patterns = {
            p for s in
            [
                guild_patterns.get(r, [])
                for r in user_roles
            ] for p in s
        }

        patterns = {p for p in raw_patterns if not p.startswith('!')}
        antipatterns = {p[1:] for p in raw_patterns if p.startswith('!')}

        if is_dev:
            patterns.add('*')
            antipatterns.clear()

        permissions = {p for s in [self.matcher(
            pattern) for pattern in patterns] for p in s}

        antipermissions = {p for s in [self.matcher(
            pattern) for pattern in antipatterns] for p in s}

        user_permissions = permissions - antipermissions

        if is_dev:
            user_permissions.add('dev')

        return user_permissions

    async def check(self, pattern: str, user: Member, guild: Guild) -> bool:
        if pattern != 'dev' and user.guild_permissions.administrator:
            return True

        return bool(
            self.matcher(
                pattern,
                await self.user(user, guild)
            )
        )
