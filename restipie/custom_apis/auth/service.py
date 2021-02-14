import json
from datetime import datetime, timedelta

import jwt
import frappe
from frappe.exceptions import ValidationError


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
		raise ValidationError("{} already in used.".format(email))


def validate_mobile_no(mobile_no):
	duplicates = frappe.get_list(
		"User",
		filters={"mobile_no": mobile_no},
		fields="name"
	)

	if duplicates:
		raise ValidationError("{} already in used.".format(mobile_no))


def simple_login(*args, **kwargs):
	data = kwargs.get("data")
	email = data.get("email")
	password = data.get("password")

	user_id = frappe.utils.password.check_password(email, password)
	frappe.local.login_manager.login_as(email)
	update_session_data()

	user = get_user(user_id)
	user["id"] = user_id
	user["email"] = email
	user["token"] = generate_token(user_id)

	return user


def get_user(email):
	user = frappe.get_doc("User", email)
	return {
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


def validate_password(currentPassword, newPassword, confirmPassword):
	confirmed = (newPassword == confirmPassword)
	same_passwords = currentPassword == newPassword and confirmed
	if same_passwords:
		return { "message": "New password cannot be the same with your old password." }
	if not confirmed:
		return { "message": "Please confirm your password." }


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
