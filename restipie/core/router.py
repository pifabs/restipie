# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from werkzeug.routing import Map, Rule


class CustomRouter():
	__instance = None
	__router = {}
	__url_map = None
	__private_endpoints = []

	def __init__(self):
		""" Virtually private constructor. """
		if CustomRouter.__instance is not None:
			raise Exception("This class is a singleton!")
		else:
			CustomRouter.__instance = self
			self.__url_map = Map()

	def get_instance():
		if not CustomRouter.__instance:
			CustomRouter()
		return CustomRouter.__instance

	def set_route(self, method, path, handler, middlewares=(), private=True):
		key = "%s:%s" % (method.upper(), path)
		self.__router[key] = (handler, middlewares)
		self.__url_map.add(Rule(path, endpoint=path, strict_slashes=False))

		if private:
			self.__private_endpoints.append(key)

	def get_handler(self, method, path):
		key = "%s:%s" % (method.upper(), path)
		return self.__router.get(key, (None, None))

	def get_router(self):
		return self.__router.copy()

	def get_private_urls(self):
		return tuple(self.__private_endpoints)

	def adapter_match(self):
		return self.__url_map.bind_to_environ(frappe.request.environ).match()
