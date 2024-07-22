from .subcog import ExtensionMediaLinkFixerSubCog
from .classes import MediaFixer
from regex import findall


fixers = [
	MediaFixer(r'(twitter|x)\.com','fxtwitter.com'),
	MediaFixer(r'instagram\.com','ddinstagram.com',wait_time=7),
	MediaFixer(r'tiktok\.com','tnktok.com',wait_time=10)
]

class ExtensionMediaLinkFixerLogic(ExtensionMediaLinkFixerSubCog):
	def find_fixes(self,content:str) -> list[MediaFixer]:
		fixes = []
		for fix in fixers:
			if fix.only_if_includes and fix.only_if_includes not in content: continue
			if findall(f'(?<!<)https:\/\/(.*\.)?{fix.find}',content):
				fixes.append(fix)
		return fixes
			