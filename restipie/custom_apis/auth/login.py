import json
from datetime import datetime, timedelta

import jwt
import frappe
from frappe import _
from werkzeug.exceptions import HTTPException, NotFound, BadRequest, Unauthorized
from frappe.core.doctype.user.user import (handle_password_test_fail,
										   test_password_strength)
from restipie.custom_api_core import request


@request.api("POST", "/v1/api/login")
def login(*args, **kwargs):
	# todo validate number of allowed sessions
	data = kwargs.get("data")
	email = data.get("email")
	password = data.get("password")

	user = frappe.utils.password.check_password(email, password)
	frappe.local.login_manager.login_as(email)
	_user = get_user(user)
	_user["id"] = user
	_user["email"] = email
	_user["token"] = generate_token(user)

	update_session_data()
	return  _user


def get_user(email):
	user = frappe.get_doc("User", email)
	driver = frappe.get_doc("Driver", {"user": user.name})
	return {
		"carrierId": driver.name,
		"firstName": user.first_name,
		"lastName": user.last_name,
		"phone": driver.cell_number,
		"vehicleId": driver.vehicle,
		"plateNumber": driver.vehicle,
		"type": "DISPATCHER"
	}


def update_session_data():
	session_data = frappe.session.data
	sid = frappe.session.sid

	session_data["session_expiry"] = "8640:00:00"
	session_data["device"] = "mobile"
	session_data["session_country"] = "PH"

	stmt = """
		UPDATE `tabSessions`
		SET sessiondata = "{session_data}",
		device = "{device}"
		where sid = "{sid}"
	""".format(
		session_data=json.dumps(session_data).replace("\"", "\'"),
		device=session_data.get("device"),
		sid=sid
		)

	frappe.db.sql(stmt)
	frappe.db.commit()
	frappe.cache().hset("session", sid, session_data)


def generate_token(user):
	jwt_secret = frappe.local.conf.get('jwt_secret')
	jwt_alg = frappe.local.conf.get('jwt_alg')

	return jwt.encode({
		"algorithm":jwt_alg,
		"iss": "codedisruptors",
		"aud":"lyff mobile app",
		# "exp": datetime.utcnow() + timedelta(days=1),
		"iat": datetime.timestamp(datetime.now()),
		"user": user,
		"sid": frappe.session.sid
		},
		jwt_secret,
	).decode("utf-8")


def validate_password(currentPassword, newPassword, confirmPassword):
	confirmed = (newPassword == confirmPassword)
	same_passwords = currentPassword == newPassword and confirmed
	if same_passwords:
		return { "message": "New password cannot be the same with your old password." }
	if not confirmed:
		return { "message": "Please confirm your password." }

	if len(newPassword) < 8 or len(newPassword) > 100:
		return { "message": "Password length should be between 8 and 100 characters long" }


def check_password_strength(user, new_password):
	user = frappe.get_doc("User", user)
	user_data = (
		user.first_name,
		user.middle_name,
		user.last_name,
		user.email,
		user.birth_date
	)

	result = test_password_strength(new_password=new_password, user_data=user_data)
	feedback = result.get("feedback", None)

	if feedback and not feedback.get('password_policy_validation_passed', False):
		handle_password_test_fail(result)
