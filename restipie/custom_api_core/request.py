from .router import CustomRouter


def api(method, path, middlewares=()):
	"""Registers a function and its middlewares.

	:param method: str
		Valid http method
	:param path: str
		The url path to which the decorated function should be mapped.
	:param middlewares: Iterable
		An iterable containing functions that will be called before executing the decorated function.


		Example:

		@api("GET", "/api/custom/ping", middlewares=[authenticate])
		def ping(*args, **kwargs):
			return "pong"
	"""
	def inner_fn(handler):
		CustomRouter.get_instance().set_route(
			method.upper(),
			path,
			handler,
			middlewares=middlewares
		)
	return inner_fn
