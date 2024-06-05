from discord import Member

class ActivityRoleChanges:
	def __init__(
		self,
		added: set[Member]|None = None,
		removed: set[Member]|None = None,
		unchanged: set[Member]|None = None
	) -> None:
		self.added = added or set()
		self.removed = removed or set()
		self.unchanged = unchanged or set()

	@property
	def total_users(self) -> int:
		return sum([
			len(self.added),
			len(self.removed),
			len(self.unchanged)])