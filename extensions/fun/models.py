from dataclasses import dataclass
from discord import User, Member


@dataclass
class Reminder:
    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.id == other.id

    def __hash__(self) -> int:
        return hash(f'{self.user.id}::{self.trigger_time}::{self.reminder}')

    user: User | Member
    trigger_time: float
    reminder: str
