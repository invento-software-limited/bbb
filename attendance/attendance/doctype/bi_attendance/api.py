import  frappe
import requests
import json
# from frappe import enqueue
#
# @frappe.whitelist()
# def sync_attendance_data():
#     method = 'attendance.attendance.doctype.bi_attendance.api.get_attendance_data'
#     task = enqueue(method=method, queue='default', timeout=200)
#     print("============>>", task)
#     frappe.msgprint("Syncing the all new attendances")
#     return True


def get_token():
    login_url = 'http://bibrands.inv-pos.com/index.php/api/v1/login/'
    headers = {
        'content-type': 'application/json',
    }
    credential = {
        "username": "munim_ba",
        "password": "12345678"
    }

    response = requests.post(login_url, json=credential, headers=headers).json()

    if response["code"] == 200:
        return response['data']['login']['token']

    return "Credential doesn't match"


@frappe.whitelist()
def get_attendance_data():
    url = 'http://bibrands.inv-pos.com/index.php/api/v1/attendances/list?offset=20&limit=2'
    headers = {
        'content-type': 'application/json',
        'Authorization': get_token()
    }

    response = requests.get(url, headers=headers).json()

    if response['code'] == 200:
        attendance_data = response['data'].get('attendances')

        for attendance in attendance_data:
            attendance['name'] = None
            attendance_obj_exists = frappe.db.exists("BI Attendance", {"attendance_id":attendance['attendance_id']})
            print(f"========= {attendance_obj_exists} =========")

            if attendance_obj_exists:
                attendance_obj = frappe.get_doc("BI Attendance", attendance_obj_exists)

                for attr, value in attendance.items():
                    setattr(attendance_obj, attr, value)

                attendance_obj.save()
            else:
                print("============= Not Exists =============")
                attendance_obj = frappe.new_doc("BI Attendance")

                for attr, value in attendance.items():
                    setattr(attendance_obj, attr, value)

                attendance_obj.insert()
                # attendance_obj.submit()

        frappe.db.commit()
        return attendance_data

    return "Something went wrong"