from utils.pycord_classes import SubView


class AutoResponseOverridesView(SubView):
	def __init__(self,*args,**kwargs) -> None:
		error = NotImplementedError('auto response overrides not implemented yet!')
		error.add_note('suppress')
		raise error