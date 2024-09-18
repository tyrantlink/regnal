from dataclasses import dataclass


@dataclass(frozen=True)
class MediaFixer:
    find: str
    replace: str
    only_if_includes: str | None = None
    clear_embeds: bool = True
    wait_time: int = 5
    remove_params: bool = True
