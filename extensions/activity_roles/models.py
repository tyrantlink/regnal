from discord import Member

class ActivityRoleChanges:
	def __init__(
		self,
		added: set[Member] = set(),
		removed: set[Member] = set(),
		unchanged: set[Member] = set()
	) -> None:
		self.added = added
		self.removed = removed
		self.unchanged = unchanged

	@property
	def total_users(self) -> int:
		return sum([
			len(self.added),
			len(self.removed),
			len(self.unchanged)])