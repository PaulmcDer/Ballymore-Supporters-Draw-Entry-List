import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

SHEET_ID = "1umG0zNs4Uz9IqfZXPXEeAgfSWoRTzDDsEwlSRC-3PnM"

st.set_page_config(
    page_title="Supporters Monthly Draw Ticket entry",
    page_icon="🏐",
    layout="centered"
)

# --------------------------------------------------
# GOOGLE SHEETS CONNECTION
# --------------------------------------------------

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(SHEET_ID).sheet1

# --------------------------------------------------
# PAGE
# --------------------------------------------------

col1, col2, col3 = st.columns([2, 1.5, 2])

with col2:
    st.image(
        "logo.png",
        width=140
    )

st.title("Supporters Monthly Draw Tickets")

st.write(
    "Please enter the ticket holder's details below and click Submit Entry when complete."
)

if "name" not in st.session_state:
    st.session_state.name = ""

if "phone" not in st.session_state:
    st.session_state.phone = ""

if "ticket" not in st.session_state:
    st.session_state.ticket = ""

if "seller" not in st.session_state:
    st.session_state.seller = ""

if "comments" not in st.session_state:
    st.session_state.comments = ""

if "paid" not in st.session_state:
    st.session_state.paid = "Not Paid"

if "show_success" not in st.session_state:
    st.session_state.show_success = False

if "reset_form" not in st.session_state:
    st.session_state.reset_form = False

if st.session_state.reset_form:
    st.session_state.name = ""
    st.session_state.phone = ""
    st.session_state.ticket = ""
    st.session_state.seller = ""
    st.session_state.comments = ""
    st.session_state.paid = "Not Paid"   # or whatever default you want
    st.session_state.reset_form = False 

# --------------------------------------------------
# FORM
# --------------------------------------------------

with st.form(
    "draw_entry_form",
    clear_on_submit=False

    ):

    name = st.text_input(
        "Name",
        key="name"
    )

    seller = st.text_input(
        "Seller Name (Required)",
        key="seller"
    )

    phone = st.text_input(
        "Ticket Holder Contact Number",
        key="phone"
    )

    ticket = st.text_input(
        "Ticket Number",
        key="ticket"
    )

    paid = st.selectbox(
        "Payment Method",
        [
            "Not Paid",
            "Paid by revolut",
            "Paid by BOI",
            "Paid by Cash/Cheque",
        ],
        key= "paid"
    )

    comments = st.text_area(
        "Comments / Notes (Optional)",
        max_chars=200,
        key= "comments"
    )

    submit = st.form_submit_button(
        "Submit Entry"
    )


#--------------------------------------------------
# New Section 
#--------------------------------------------------

if st.session_state.show_success:

    st.success(
            "✅ Entry submitted successfully. You can now enter another ticket if required."
    )
    st.session_state.show_success = False

# --------------------------------------------------
# PROCESS ENTRY
# --------------------------------------------------

if submit:

    st.session_state.show_success = False

    name = name.strip()
    phone = phone.strip().replace(" ", "")
    ticket = ticket.strip()

    if not name:

        st.error(
            "Please enter a name."
        )

    elif phone and not phone.isdigit():

        st.error(
            "Phone number must contain numbers only."
        )
    elif not seller:
        st.error(
            "Please enter a seller name"
        )

    elif phone and len(phone) != 10:

        st.error(
            "Phone number must be 10 digits."
        )

    elif not ticket:

        st.error(
            "Please enter a ticket number."
        )

    else:

        if not ticket.upper().startswith("T"):
            ticket = f"T{ticket}"

        existing_phones = [
            str(x).strip().replace(" ", "")
            for x in sheet.col_values(4)[1:]
        ]

        phone_check = phone

        if phone_check and phone_check in existing_phones:

            st.error(
                f"{phone} already exists."
            )

        else:

            timestamp = datetime.now().strftime(
                "%d/%m/%Y %H:%M"
            )
            
            sheet.append_row(
                [
                    name,
                    seller,
                    ticket,
                    phone,
                    paid,
                    timestamp,
                    comments
                ]
            )
            st.session_state.reset_form = True
            st.session_state.show_success = True
            
            st.rerun()
# --------------------------------------------------
# VIEW ENTRIES
# --------------------------------------------------

st.markdown("---")
st.subheader("View Submitted Entries")

search_seller = st.text_input(
    "Enter Seller Name",
    key="search_seller"
)

if st.button("View My Entries"):

    if not search_seller.strip():
        st.warning("Please enter a seller name.")
    else:

        records = sheet.get_all_records()

        results = []

        for row in records:

            if search_seller.strip().lower() in str(row["Seller Name"]).strip().lower():

                results.append(
                    {
                        "Seller Name": row["Seller Name"],
                        "Ticket Holder": row["Name"],
                        "Ticket Number": row["Ticket Number"]
                    }
                )

        if results:

            st.metric("Total Entries", len(results))
            
            st.dataframe(
                results,
                width="stretch"
            )
        else:
            st.info("No entries found for that seller.")

# --------------------------------------------------
# ADMIN VIEW
# --------------------------------------------------

st.markdown("---")
st.subheader("Admin Access")

admin_pin = st.text_input(
    "Admin PIN",
    type="password"
)

if st.button("View Full Table"):

    if admin_pin == st.secrets["ADMIN_PIN"]:

        records = sheet.get_all_records()
        records.reverse()

        results = []

        for row in records:

            results.append(
                {
                    "Seller Name": row["Seller Name"],
                    "Ticket Holder": row["Name"],
                    "Ticket Number": row["Ticket Number"],
                    "Paid": row["Paid"]
                }
            )

        st.success(f"{len(results)} entries found.")

        st.dataframe(
            results,
            width="stretch"
        )

    else:
        st.error("Invalid PIN.")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Ballymore GAA Supporters Monthly Draw Ticket Entry System"
)

