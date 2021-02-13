import importlib
import pathlib

try:
	from importlib import resources
except ImportError:
	import importlib_resources as resources


def _import(package, plugin):
	"""Import the given plugin file from a package"""
	importlib.import_module(f"{package}.{plugin}")

def _import_all(package):
	"""Import all plugins in a package"""
	files = resources.contents(package)
	plugins = [f[:-3] for f in files if f.endswith(".py") and f[0] != "_"]
	for plugin in plugins:
		_import(package, plugin)
