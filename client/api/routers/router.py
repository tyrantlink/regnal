from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..crapi import CrAPI


class CrAPIRouter:
    def __init__(self, crapi: 'CrAPI') -> None:
        self.crapi = crapi
        self.session = crapi.session
