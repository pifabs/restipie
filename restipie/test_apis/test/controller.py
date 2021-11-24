import frappe

from restipie.core import request
from restipie.test_apis.api_version import API_V1

USERS_PATH = f"{API_V1}/test/users"
USER_BY_ID_PATH = f"{USERS_PATH}/<id>"


@request.api("POST", USERS_PATH)
def create_user(*args, **kwargs):
	try:
		data = kwargs.get("data")

		# do some magic

		frappe.local.response.http_status_code = 201
		return data
	except Exception as e:
		raise e


@request.api("GET", USERS_PATH)
def get_all_users(*args, **kwargs):
	try:
		qs = kwargs.get("query_strings")  # noqa: F841

		# do some magic

		return []
	except Exception as e:
		raise e


@request.api("GET", USER_BY_ID_PATH)
def get_one_user(*args, **kwargs):
	try:
		user_id = kwargs.get("params").get("id")

		# do some magic

		return {"user_id": user_id}
	except Exception as e:
		raise e


@request.api("PATCH", USER_BY_ID_PATH)
def update_user(*args, **kwargs):
	try:
		user_id = kwargs.get("params").get("id")

		# do some magic

		return {"user_id": user_id}
	except Exception as e:
		raise e


@request.api("DELETE", USER_BY_ID_PATH)
def delete_user(*args, **kwargs):
	try:
		user_id = kwargs.get("params").get("id")  # noqa: F841

		# do some magic

		frappe.local.response.http_status_code = 202
		return "ok"
	except Exception as e:
		raise e
