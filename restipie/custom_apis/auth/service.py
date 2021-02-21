import json
from datetime import datetime, timedelta

import jwt, pyotp
import frappe
from frappe import _
from frappe.utils.background_jobs import enqueue
from frappe.core.doctype.user import user
from frappe.exceptions import ValidationError
from frappe.twofactor import (
	should_run_2fa,
	authenticate_for_2factor,
	get_cached_user_pass,
	two_factor_is_enabled_for_,
	confirm_otp_token,
	get_otpsecret_for_,
	get_verification_obj
)

from werkzeug.exceptions import NotImplemented


def create_account(*args, **kwargs):
	frappe.set_user("Administrator")

	email = kwargs.get("email")
	mobile_no = kwargs.get("mobile_no")

	validate_email(email)
	validate_mobile_no(mobile_no)

	user = frappe.get_doc({
		"doctype": "User",
		"first_name":kwargs.get("fullname"),
		"location": kwargs.get("location"),
		"email": email,
		"mobile_no": mobile_no
	})

	user.append_roles("Customer")
	user.save()
	frappe.db.commit()

	return user


def validate_email(email):
	duplicates = frappe.get_list("User", filters={"name": email}, fields="name")

	if duplicates:
		raise ValidationError("Email or mobile no. already in used.")


def validate_mobile_no(mobile_no):
	duplicates = frappe.get_list(
		"User",
		filters={"mobile_no": mobile_no},
		fields="name"
	)

	if duplicates:
		raise ValidationError("Email or mobile no. already in used.")


def simple_login(*args, **kwargs):
	data = kwargs.get("data")
	email = data.get("email")
	password = data.get("password")

	user_id = frappe.utils.password.check_password(email, password)
	return handle_session(email)


def get_user(email):
	user = frappe.get_doc("User", email)
	return {
		"_id": user._id,
		"fullname": user.first_name,
		"location": user.location
	}


def update_session_data():
	session_data = frappe.session.data
	sid = frappe.session.sid

	session_data["session_expiry"] = "8640:00:00"
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
	jwt_secret = frappe.local.conf.get('jwt_secret', "secret")
	jwt_alg = frappe.local.conf.get('jwt_alg', "HS256")
	site = frappe.local.site_path.replace("./", "")

	return jwt.encode({
			"algorithm":jwt_alg,
			"iss": site,
			"aud": "{}-client".format(site),
			# "exp": datetime.utcnow() + timedelta(days=1),
			"iat": datetime.timestamp(datetime.now()),
			"user": user,
			"sid": frappe.session.sid
		},
		jwt_secret,
	).decode("utf-8")


def handle_session(email):
	frappe.local.login_manager.login_as(email)
	update_session_data()

	user = get_user(email)
	user["email"] = email
	user["token"] = generate_token(email)

	return user


def login_2fa(*args, **kwargs):
	if kwargs.get("data").get("login_by") == "mobile_no":
		raise NotImplemented("mobile_no not yet supported.")

	email = kwargs.get("data").get("email")
	authenticate_for_2factor(email)

	return {
		"message": "Verification code has been sent to your email.",
		"data": {"tmp_id": frappe.local.response['tmp_id']}
	}


def confirm_2fa(*args, **kwargs):
	otp = kwargs.get("data").get("otp")
	email = kwargs.get("data").get("email")
	tmp_id = kwargs.get("data").get("tmp_id")
	result = confirm_otp_token(frappe.local.login_manager,otp=otp,tmp_id=tmp_id)
	if result:
		return handle_session(email)


def logout(*args, **kwargs):
	from frappe.sessions import delete_session, clear_sessions

	token = kwargs.get("decoded")

	qs = kwargs.get("query_strings")
	if qs.get("sessions", None) == "all":
		clear_sessions(token.get("user"), force=True)
		return

	delete_session(token.get("sid"))
	return { "message" :  "Goodbye!"}


def change_password(*args, **kwargs):
	data = kwargs.get("data")
	decoded = kwargs.get("decoded")
	old_pwd = data.get("old_pwd")
	new_pwd = data.get("new_pwd")

	frappe.utils.password.check_password(decoded.get("user"), old_pwd)

	validate_password(old_pwd, new_pwd)

	check_password_strength(decoded.get("user"), new_pwd)

	passw = frappe.utils.password.update_password(
		decoded.get("user"),
		new_pwd,
		logout_all_sessions=True
	)
	
	return { "message": "Password successfully updated.", "data": None }


def validate_password(old_pwd, new_pwd):
	same_passwords = old_pwd == new_pwd
	if same_passwords:
		raise ValidationError("New password cannot be the same with your old password.")


def check_password_strength(email, new_password):
	_user = frappe.get_doc("User", email)
	user_data = (
		_user.first_name,
		_user.middle_name,
		_user.last_name,
		_user.email,
		_user.birth_date
	)

	result = user.test_password_strength(new_password=new_password, user_data=user_data)
	feedback = result.get("feedback", None)

	if feedback and not feedback.get('password_policy_validation_passed', False):
		user.handle_password_test_fail(result)


def handle_pwd_reset_request(*args, **kwargs):
	message = {
		"message": "If that email address is in our database, we will send you an email to reset your password.",
		"data": None
	}
	email = kwargs.get("email")

	try:
		user = frappe.get_cached_doc("User", {"name": email, "enabled": 1})

		user.validate_reset_password()
		enqueue(
			user.reset_password,
			queue="short",
			is_async=True,
			send_email=True
		)

		return message
	except frappe.DoesNotExistError as e:
		frappe.clear_messages()
		return message
	except Exception as e:
		raise e
