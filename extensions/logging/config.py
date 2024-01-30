if not 'TYPE_HINT': from client.config import Config
from client.config.models import ConfigOption,ConfigSubcategory,OptionType,AdditionalView,ConfigAttrs
from utils.db.documents.ext.enums import TWBFMode




def register_config(config:'Config') -> None:
	...

