from os import environ,devnull,remove
environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # needs to be before nsfw_detector import
from nsfw_detector import predict
import sys

class nsfw:
	def __init__(self) -> None:
		predict.tf.get_logger().setLevel(50)
		predict.tf.autograph.set_verbosity(0)
		self.nsfw_model = predict.load_model('nsfw_model')
		self.stdout = sys.stdout
	
	def predict(self,filepath:str) -> dict:
		return predict.classify(self.nsfw_model,filepath)

	async def is_nsfw(self,filepath:str,delete:bool=True) -> bool:
		with open(devnull,'w') as null:
			sys.stdout = null # overwrite stdout
			out = self.predict(filepath)
			sys.stdout = self.stdout # return stdout
			if delete: remove(filepath)

		for k,v in out[list(out.keys())[0]].items():
			match k:
				case 'hentai' if v > 0.125: return True
				case 'porn'   if v > 0.18: return True
				case 'sexy'   if v > 0.60: return True
				case _: pass
		return False