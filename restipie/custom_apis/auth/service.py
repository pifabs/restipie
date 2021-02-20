import json
from datetime import datetime, timedelta

import jwt
import frappe
from frappe.core.doctype.user import user
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
	frappe.local.login_manager.login_as(email)
	update_session_data()

	user = get_user(user_id)
	user["email"] = email
	user["token"] = generate_token(user_id)

	return user


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


def logout(*args, **kwargs):
	from frappe.sessions import delete_session, clear_sessions

	token = kwargs.get("decoded")
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
