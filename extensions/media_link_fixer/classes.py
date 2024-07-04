from dataclasses import dataclass

@dataclass
class MediaFixer:
	find:str
	replace:str
	only_if_includes:str = None
	clear_embeds:bool = True
	wait_time:int = 5