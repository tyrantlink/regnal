from .base import register_permissions as register_base_permissions # imported here for client to import
if not 'TYPE_HINT': from client import Client
from discord import Member,Guild
from typing import Iterable
from re import match

class PermissionHandler:
	def __init__(self,client:'Client') -> None:
		self.client = client
		self.permissions = set()
		register_base_permissions(self)

	def register_permission(self,permission:str) -> None:
		self.permissions.add(permission)
		self.client.log.debug(f'registered permission {permission}')

	def unregister_permission(self,permission:str) -> None:
		self.permissions.discard(permission)
		self.client.log.debug(f'unregistered permission {permission}')

	def matcher(self,pattern:str,check:Iterable[str]=None) -> set[str]:
		check = check if check is not None else self.permissions
		pattern = pattern.replace('.','\.').replace('*','.*')
		return set(filter(lambda p: match(f'^{pattern}$',p),check))

	async def user(self,user:Member,guild:Guild) -> set[str]:
		guild_patterns = (await self.client.db.guild(guild.id)).data.permissions
		user_roles = {str(r.id) for r in user.roles if str(r.id) in guild_patterns}
		if str(user.id) in guild_patterns: user_roles.add(str(user.id))
		is_dev = user.id in self.client.owner_ids and self.client.project.config.dev_bypass
		user_patterns = {p for s in [guild_patterns.get(r,[]) for r in user_roles] for p in s}
		# if is_dev: user_patterns.add('*')
		user_permissions = {p for s in [self.matcher(pattern) for pattern in user_patterns] for p in s}
		if is_dev: user_permissions.add('dev')
		return user_permissions

	async def check(self,pattern:str,user:Member,guild:Guild) -> bool:
		return user.guild_permissions.administrator or bool(self.matcher(pattern,await self.user(user,guild)))
		return bool(self.matcher(pattern,await self.user(user,guild)))
