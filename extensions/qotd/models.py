from pydantic import BaseModel,Field
from typing import Optional
from enum import Enum

class QOTDRollType(Enum):
	RANDOM = 0
	SEQUENTIAL = 1
	RANDOM_ACTIVE_MEMBER = 2

class QOTDExpiry(Enum):
	NONE = 0
	INDEX = 1
	REGEX = 2

class QOTDPack(BaseModel):
	roll_type:QOTDRollType
	expiry:QOTDExpiry
	expiry_id:Optional[int] = Field(None,description='expiry id\n\nif expiry is index, this is None\nif expiry is regex, this is the regex match group index')
	questions:list[str]