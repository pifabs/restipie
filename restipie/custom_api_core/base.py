class Base(object):
	def __init__(self, **kwargs):
		self.valid_fields = []
		self.map_fields(kwargs)

	def map_fields(self, object):
		for key, value in object.items():
			if key in self.valid_fields:
				setattr(self, key, value)

	def json(self):
		return json.dumps(self.as_dict())

	def as_dict(self):
		copy =  self.__dict__
		if hasattr(copy, "valid_fields"):
			delattr(copy, "valid_fields")
		return copy
