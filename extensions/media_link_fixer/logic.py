from .subcog import ExtensionMediaLinkFixerSubCog
from .classes import MediaFixer
from regex import findall


fixers = [
	MediaFixer(r'tiktok\.com','tiktokez.com')
]

class ExtensionMediaLinkFixerLogic(ExtensionMediaLinkFixerSubCog):
	def find_fixes(self,content:str) -> list[MediaFixer]:
		fixes = []
		for fix in fixers:
			if fix.only_if_includes and fix.only_if_includes not in content: continue
			if findall(fix.find,content):
				fixes.append(fix)
		return fixes
			