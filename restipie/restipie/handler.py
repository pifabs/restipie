import json

import frappe

from werkzeug.exceptions import NotImplemented

from restipie.custom_api_core import response, router


def handle(*args, **kwargs):
	method = kwargs.get("method")
	path = kwargs.get("path")
	endpoint = kwargs.get("endpoint")

	fn, middlewares = router.CustomRouter.get_instance().get_handler(method, endpoint)
	if not fn:
		raise NotImplemented(
			"This server does not support the action you requested."
		)

	mwargs = args
	mwkwargs = kwargs
	for middleware in middlewares:
		mwargs, mwkwargs = middleware(*mwargs, **mwkwargs)

		if "errors" in mwkwargs and len(mwkwargs.get("errors")):
			return response.as_json(
				status_code=417,
				data={
					"success": False,
					"context": "ValidationError",
					"errors": mwkwargs.get("errors")
				}
			)

	result = fn(*mwargs, **mwkwargs)
	return response.as_json(data=result.as_dict())
