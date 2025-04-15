import frappe
import requests


@frappe.whitelist(allow_guest = True, methods=["POST"])
def create_member_registration(**kwargs):
    try:
        member_registration = frappe.get_doc({
            "doctype": "Member Registration",
            "id_number": kwargs.get('id_number'),
            "mobile_number": kwargs.get('mobile_number'),
            "full_name": kwargs.get('full_name'),
            "email_address": kwargs.get('email_address'),
            "kra_pin": kwargs.get('kra_pin'),
            "membership_type": kwargs.get('membership_type')
        })
        member_registration.insert()
        frappe.db.commit()
        if member_registration.name:
            default_company = frappe.defaults.get_user_default("Company")
            full_name = kwargs.get('full_name')
            first_name = full_name.split()[0].capitalize()

            message = (
                    f"Welcome to {default_company}, {first_name}! Once your registration is approved, "
                    "you will receive your login credentials. Let us know if you have any questions!"
                )

            
            send_sms(kwargs.get('mobile_number'), message)


            return {'status': 200, 'message': "Registration received successfully"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        return {'error': str(e)}, 400
    

def send_sms(mobile, message):
    url = "https://sms.textsms.co.ke/api/services/sendsms/"
    data = {
        "apikey": "6bf53f0bda4924760fb1b2e018e2960d",
        "partnerID": "9546",
        "shortcode": "LEGEND SOFT",
        "mobile": format_mobile_number(mobile),
        "message": message
    }
    
    return requests.get(url, params=data)

def format_mobile_number(mobile):
    mobile = mobile.replace(" ", "")
    filtered_mobile = mobile[-9:]
    mobile = "254" + filtered_mobile
    return mobile


@frappe.whitelist( allow_guest=True )
def login(usr, pwd):
    try:
        try:
            login_manager = frappe.auth.LoginManager()
            login_manager.authenticate(user=usr, pwd=pwd)
            login_manager.post_login()
        except frappe.exceptions.AuthenticationError:
            frappe.clear_messages()
            frappe.local.response["message"] = {
                "success_key":0,
                "message":"Authentication Error!"
            }

            return

        api_generate = generate_keys(frappe.session.user)
        user = frappe.get_doc('User', frappe.session.user)

        frappe.response["message"] = {
            "success_key":1,
            "message":"Authentication success",
            "sid":frappe.session.sid,
            "api_key":user.api_key,
            "api_secret":api_generate,
            "username":user.username,
            "email":user.email,
            "base_url": frappe.utils.get_url()
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error in login: {e}")
        return {"status": "error", "message": str(e)}


def generate_keys(user):
    try:
        user_details = frappe.get_doc('User', user)
        api_secret = frappe.generate_hash(length=15)

        if not user_details.api_key:
            api_key = frappe.generate_hash(length=15)
            user_details.api_key = api_key

        user_details.api_secret = api_secret
        user_details.save()

        return api_secret
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error in login: {e}")
        return {"status": "error", "message": str(e)}