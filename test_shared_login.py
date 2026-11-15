import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class Worksheet:
    def __init__(self, records):
        self.records = records

    def get_all_records(self):
        return self.records


class SharedLoginTests(unittest.TestCase):
    def test_shared_login_and_independent_access(self):
        sheets = {
            "Ticket_Entries": Worksheet([{
                "Name": "Test Person", "Seller Name": "Seller One",
                "Ticket Number": "T1", "Phone": "0851234567", "Paid": "Not Paid",
            }]),
            "Last_Year_Tickets": Worksheet([{"Seller": "Seller One", "Name": "Last Year"}]),
            "Users": Worksheet([{"Username": "Seller One", "PIN": "5678"}]),
        }
        with patch("gspread.authorize") as authorize, patch(
            "google.oauth2.service_account.Credentials.from_service_account_info"
        ):
            authorize.return_value.open_by_key.return_value.worksheet.side_effect = sheets.get
            app = AppTest.from_file("App.py")
            app.secrets["SAVE_PIN"] = "1234"
            app.secrets["ADMIN_PIN"] = "9999"
            app.secrets["REVOLUT_LINK"] = "https://example.com"
            app.secrets["gcp_service_account"] = {}
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(app.button(key="FormSubmitter:draw_entry_form-✅ Submit Entry").disabled)
            self.assertFalse(app.session_state.save_pin_ok)

            app.text_input[0].set_value("0000")
            app.button(key="FormSubmitter:shared_login_form-🔓 Login").click().run()
            self.assertFalse(app.session_state.save_pin_ok)
            self.assertTrue(any("Incorrect PIN" in error.value for error in app.error))

            app.text_input[0].set_value("1234")
            app.button(key="FormSubmitter:shared_login_form-🔓 Login").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(app.session_state.save_pin_ok)
            self.assertFalse(app.button(key="FormSubmitter:draw_entry_form-✅ Submit Entry").disabled)
            self.assertTrue(any("Tickets Last Year" in metric.label for metric in app.metric))
            self.assertTrue(any("Total Entries" in metric.label for metric in app.metric))
            self.assertFalse(app.session_state.admin_pin_ok)
            self.assertFalse(app.session_state.seller_logged_in)

            app.button(key="shared_logout").click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.session_state.save_pin_ok)
            self.assertTrue(app.button(key="FormSubmitter:draw_entry_form-✅ Submit Entry").disabled)
            self.assertFalse(any("Tickets Last Year" in metric.label for metric in app.metric))
            self.assertFalse(any("Total Entries" in metric.label for metric in app.metric))


if __name__ == "__main__":
    unittest.main()