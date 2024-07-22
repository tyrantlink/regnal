from .ClientLarge import ClientLarge
from .ClientSmall import ClientSmall
from .config import Config

Client = ClientLarge | ClientSmall
