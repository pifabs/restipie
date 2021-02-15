import frappe

from restipie.custom_api_core import request
from restipie.custom_api_core import response
from restipie.custom_api_core.middleware import authenticate

from . import service


@request.api("DELETE", "/v1/api/logout", middlewares=(authenticate,))
def logout(*args, **kwargs):
	try:
		service.logout(**kwargs)

		return response.JSONResponse(
			status_code=200,
			message="Logged out successfully!",
			data={}
		)
	except Exception as e:
		raise e
