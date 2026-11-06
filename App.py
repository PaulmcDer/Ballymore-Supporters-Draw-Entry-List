import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
#from streamlit_extras.metric_cards import style_metric_cards

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

SHEET_ID = "1umG0zNs4Uz9IqfZXPXEeAgfSWoRTzDDsEwlSRC-3PnM"

st.set_page_config(
    page_title="Supporters Monthly Draw Tickets",
    page_icon="logo.png",
    layout="centered"
)
st.logo("logo.png")
import base64

def get_base64_logo():
    with open("logo.png", "rb") as f:
        return base64.b64encode(f.read()).decode()

logo = get_base64_logo()

# -------------------------------
# LOAD GLOBAL CSS
# -------------------------------
with open(".streamlit/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
st.markdown(f"""
<header class="app-header">
    <img src="data:image/png;base64,{logo}" alt="Ballymore GAA crest">
    <div>
        <h1>Ballymore Supporters Draw</h1>
        <p>Seller ticket entry and draw management</p>
    </div>
</header>
""", unsafe_allow_html=True)


# --------------------------------------------------
# GOOGLE SHEETS CONNECTION & CACHE ALL RECORDS / TIME
# --------------------------------------------------

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    return gspread.authorize(creds)

@st.cache_resource
def get_worksheets():
    spreadsheet = get_client().open_by_key(SHEET_ID)
    return (
        spreadsheet.worksheet("Ticket_Entries"),
        spreadsheet.worksheet("Last_Year_Tickets"),
        spreadsheet.worksheet("Users"),
    )

sheet, last_year_sheet, users_sheet = get_worksheets()

@st.cache_data(ttl=60)
def get_records():
    return sheet.get_all_records()

def get_phone_numbers():
    ticket_records = get_records()
    if not ticket_records:
        return []

    phone_column = tuple(ticket_records[0])[3]
    return [
        str(record.get(phone_column, "")).strip().replace(" ", "")
        for record in ticket_records
    ]

@st.cache_data(ttl=3600)  # 1 hour
def get_last_year_records():
    return last_year_sheet.get_all_records()

@st.cache_data(ttl=300)
def load_users():
    return users_sheet.get_all_records()

# Add a new seller to the Users sheet once, with a blank PIN for an admin to set.
def ensure_seller_user(new_seller_name):
    seller_key = new_seller_name.strip().casefold()
    user_records = users_sheet.get_all_records()

    if any(
        str(user.get("Username", "")).strip().casefold() == seller_key
        for user in user_records
    ):
        return

    users_sheet.append_row([new_seller_name, ""])
    load_users.clear()

records = get_records()
ticket_count = len(records)
# --------------------------------------------------
# FIND TOTAL WEB TICKET NUMBERS
# --------------------------------------------------

web_numbers = []

for row in records:

    ticket = str(
        row.get("Ticket Number", "")
    )

    if ticket.startswith("WEB-"):

        try:
            web_numbers.append(
                int(
                    ticket.replace(
                        "WEB-",
                        ""
                    )
                )
            )
        except:
            pass

next_web_ticket = max(
    web_numbers,
    default=0
) 

online_ticket_count = len(web_numbers)
# --------------------------------------------------
# SIDEBAR CONTENT
# --------------------------------------------------
with st.sidebar:

    # Logo
    col1, col2, col3 = st.columns([2,3,2])
    with col2:
        st.image("logo.png", width=120)

    st.markdown(
        "<h3 style='text-align:center;'>Ballymore GAA Draw Information</h3>",
        unsafe_allow_html=True
    )

    st.metric("🎟 Total Online Tickets Purchased", online_ticket_count)
    st.metric("🎟 Total Ticket Count", ticket_count)

    st.markdown("---")

    # Yellow notice
    st.markdown("""
    <div style="
        background:#FFD700;
        padding:15px;
        border-radius:10px;
        border:3px solid #b8860b;
        text-align:center;">
        🛡️ This app is for Ballymore GAA ticket sellers and Authorised club members.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.link_button(
        " 💳 Get Ballymore Draw Tickets Online 💳",
        "https://ballymore-supporters-draw-entry-list-dv6ewrazn6cbzzfgrd7jvc.streamlit.app/"
     )
# --------------------------------------------------
# Spilt for Tabs
# --------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "🎟 Ticket Entry",
        "📋 Last Year's Sales",
        "💳 Payment",
        "📊 Dashboard",
        "🔐 Admin"
        
    ]
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "save_pin_ok" not in st.session_state:
    st.session_state.save_pin_ok = False
    
if "seller_pin_ok" not in st.session_state:
    st.session_state.seller_pin_ok = False
    
# --------------------------------------------------
# PAGE
# --------------------------------------------------
with tab1:
        
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
        st.session_state.comments = ""
        st.session_state.paid = "Not Paid"   # or whatever default you want
        st.session_state.reset_form = False

    # --------------------------------------------------
    # Seller pin
    # --------------------------------------------------
    st.markdown("---")

    seller_pin = st.text_input(
        "Seller PIN",
        type="password",
        max_chars=4,
        key="seller_pin"
    )

    if seller_pin == st.secrets["SAVE_PIN"]:
        st.session_state.seller_pin_ok = True
        st.success("PIN accepted")

    elif seller_pin == "":
        st.session_state.seller_pin_ok = False

    else:
        st.session_state.seller_pin_ok = False
        st.error("Incorrect PIN")

    if not st.session_state.seller_pin_ok:
        
        #This is html which allows colour options#
        st.markdown("""
<div style="
    background:#FFF8CC;
    color:black;
    padding:14px;
    border-radius:10px;
    border:2px solid #FFD700;
    text-align:center;
    font-style: italic;
    font-family: 'Georgia', serif;
    font-weight:500;
    font-size: 15px;
">
    🔑 Enter Seller PIN to enable ticket entry and for viewing seller tickets.
</div>
""", unsafe_allow_html=True)
# --------------------------------------------------
# FORM
# --------------------------------------------------

    with st.form(
        "draw_entry_form",
        clear_on_submit=False

        ):

        st.markdown("#### Ticket details")
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

        st.markdown("#### Payment and notes")
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
            "Submit Entry",
            disabled=not st.session_state.seller_pin_ok
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
# st.session_state. is a variable that Streamlit remembers between reruns

    if submit:

        st.session_state.show_success = False

        name = name.strip()
        seller = seller.strip()
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

            existing_phones = get_phone_numbers()

            phone_check = phone

            if phone_check and phone_check in existing_phones:

                st.error(
                    f"{phone} already exists."
                )

            else:

                # Register new sellers before saving their ticket entry.
                ensure_seller_user(seller)

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
                get_records.clear()
                st.session_state.reset_form = True
                st.session_state.show_success = True
                
                
                st.rerun()

    if st.session_state.seller_pin_ok:
        st.markdown("---")
        st.subheader("View tickets by seller")

        seller_names_by_key = {}
        for row in records:
            seller_name = str(row.get("Seller Name", "")).strip()
            if seller_name:
                seller_names_by_key.setdefault(
                    seller_name.casefold(),
                    seller_name
                )

        seller_names = sorted(
            seller_names_by_key.values(),
            key=str.casefold
        )

        if seller_names:
            selected_seller = st.selectbox(
                "Select a seller",
                seller_names,
                key="entered_tickets_seller"
            )

            ticket_rows = [
                {
                    "Ticket Number": str(row.get("Ticket Number", "")).strip(),
                    "Name on Ticket": str(row.get("Name", "")).strip()
                }
                for row in records
                if str(row.get("Seller Name", "")).strip().casefold()
                == selected_seller.casefold()
            ]

            st.dataframe(
                pd.DataFrame(ticket_rows),
                hide_index=True,
                width="stretch",
                alt="Ticket numbers and ticket holder names entered by the selected seller"
            )
        else:
            st.info("No seller entries yet.")

# --------------------------------------------------
# LAST YEAR'S SALES TAB
# --------------------------------------------------

with tab2:

    st.subheader("Last Year's Tickets")

# ----------------------------------------------
# 1️⃣ SAVE TRANSACTION PIN (separate from Admin)
# ----------------------------------------------
# session_state as: Memory for this user's session
# "not in" is checking whether something doesn't exist yet.

    if "save_pin_ok" not in st.session_state:
        st.session_state.save_pin_ok = False

    if not st.session_state.save_pin_ok:

        with st.form("last_year_login"):

            save_pin = st.text_input(
                "Enter 4-digit PIN",
                type="password",
                max_chars=4
            )

            pin_login = st.form_submit_button(
                "Login"
            )

        if pin_login:

            if save_pin == st.secrets["SAVE_PIN"]:
                st.session_state.save_pin_ok = True
                st.rerun()
            else:
                st.error("Incorrect PIN")

    if st.session_state.save_pin_ok:

        col1, col2 = st.columns([6,1])

        with col1:
            st.success("Access Granted")

        with col2:
            if st.button(
                "Logout",
                key="last_year_logout"
            ):
                st.session_state.save_pin_ok = False
                st.rerun()

        records = get_last_year_records()

        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()

        seller_names = sorted(
            df["Seller"].dropna().unique()
        )

        seller = st.selectbox(
            "Select Seller",
            seller_names
        )

        filtered_df = df[
            df["Seller"] == seller
        ]

        st.metric(
            "Tickets Last Year",
            len(filtered_df)
        )

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
# --------------------------------------------------
# REVOLUT PAYMENT TAB
# --------------------------------------------------

with tab3:

    st.write("💳 Pay with Revolut")

    st.link_button(
        "💳 Pay with Revolut",
        st.secrets["REVOLUT_LINK"]
    )

    st.markdown("---")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.image(
            "revolut_qr.png",
            caption="Scan with Revolut App",
            width=250
        )

    with col2:
        st.markdown("*Bank Transfer Details (BOI)*")

        st.markdown("**Club Name**")
        st.write("BALLYMORE GAA")

        st.markdown("**IBAN**")
        st.code("IE71BOFI90177371264687")

        st.markdown("**BIC**")
        st.code("BOFIIE2DXXX ")

        st.info(
        "Please include your name as the payment reference."
        )

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
with tab4:

    st.subheader("📊 Sales Dashboard")

    save_pin = st.text_input(
        "Enter PIN to View Dashboard",
        type="password",
        max_chars=4
    )

    if save_pin == st.secrets["SAVE_PIN"]:

        records = get_records()

        if not records:
            st.info("No data available.")
            st.stop()

        df = pd.DataFrame(records)

        # -----------------------------
        # Clean Data
        # -----------------------------

        if "Paid" in df.columns:

            payment_counts = (
                df["Paid"]
                .fillna("Unknown")
                .value_counts()
            )

        # -----------------------------
        # KPI CARDS
        # -----------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "🎟 Total Tickets",
                len(df)
            )

        with col2:
            st.metric(
                "👥 Unique Sellers",
                df["Seller Name"].nunique()
            )

        with col3:
            st.metric(
                "💳 Recorded Payments",
                len(
                    df[
                        df["Paid"] != "Not Paid"
                    ]
                )
            )

        st.markdown("---")

        # -----------------------------
        # TICKETS BY PAYMENT TYPE
        # -----------------------------

        st.subheader("💳 Payment Methods")

        st.bar_chart(payment_counts)

        st.markdown("---")

        # -----------------------------
        # SELLER LEADERBOARD
        # -----------------------------

        st.subheader("🏆 Top Sellers")

        seller_counts = (
            df["Seller Name"]
            .fillna("Unknown")
            .value_counts()
        )

        st.bar_chart(seller_counts.head(10))

        st.markdown("---")

    elif save_pin != "":
        st.error("Invalid PIN")

# --------------------------------------------------
# ADMIN VIEW
# --------------------------------------------------
with tab5:

    st.markdown("---")
    st.subheader("Admin Access")

    if "admin_pin_ok" not in st.session_state:
        st.session_state.admin_pin_ok = False

    if "admin_update_message" not in st.session_state:
        st.session_state.admin_update_message = ""

    # -------------------------
    # ADMIN LOGIN
    # -------------------------
    if not st.session_state.admin_pin_ok:

        with st.form("admin_login_form"):

            admin_pin = st.text_input(
                "Admin PIN",
                type="password"
            )

            admin_login = st.form_submit_button(
                "Login"
            )

        if admin_login:

            if admin_pin == st.secrets["ADMIN_PIN"]:
                st.session_state.admin_pin_ok = True
                st.rerun()
            else:
                st.error("Invalid PIN")

    # -------------------------
    # ADMIN AREA
    # -------------------------
    if st.session_state.admin_pin_ok:

        col1, col2 = st.columns([6, 1])

        with col1:
            st.success("ADMIN LOGGED IN")

        with col2:
            if st.button(
                "Logout",
                key="admin_logout"
            ):
                st.session_state.admin_pin_ok = False
                st.rerun()

        records = get_records()

        display_records = list(reversed(records))

        results = []

        for row in display_records:
            results.append(
                {
                    "Seller Name": row["Seller Name"],
                    "Ticket Holder": row["Name"],
                    "Ticket Number": row["Ticket Number"],
                    "Paid": row["Paid"]
                }
            )

        st.info(f"{len(results)} entries found.")

        st.dataframe(
            results,
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("Update Payment Status")

        ticket_options = [
            f"{r['Ticket Number']} | {r['Name']} | {r['Seller Name']}"
            for r in display_records
        ]

        with st.form("payment_update_form"):

            selected_entry = st.selectbox(
                "Select Entry",
                ticket_options
            )

            new_status = st.selectbox(
                "New Payment Status",
                [
                    "Not Paid",
                    "Paid by revolut",
                    "Paid by BOI",
                    "Paid by Cash/Cheque"
                ]
            )

            update_status = st.form_submit_button(
                "Update Payment Status"
            )

        if st.session_state.admin_update_message:
            st.success(
                st.session_state.admin_update_message
            )
            st.session_state.admin_update_message = ""

        if update_status:

            selected_ticket = (
                selected_entry.split(" | ")[0]
            )

            row_number = None

            for idx, row in enumerate(
                records,
                start=2
            ):
                if (
                    row["Ticket Number"]
                    == selected_ticket
                ):
                    row_number = idx
                    break

            if row_number:
                
                sheet.update_cell(
                    row_number,
                    5,
                    new_status
                )

                st.session_state.admin_update_message = (
                    f"✅ {selected_ticket} updated successfully to '{new_status}'"
                )
                get_records.clear()

                st.rerun()

            else:
                st.error("Ticket not found.")

    # --------------------------------------------------
    # SELLER ACCESS
    # --------------------------------------------------

    st.markdown("---")
    st.subheader("Seller Access")

    if "seller_logged_in" not in st.session_state:
        st.session_state.seller_logged_in = False

    if "seller_name" not in st.session_state:
        st.session_state.seller_name = ""

    if "seller_update_message" not in st.session_state:
        st.session_state.seller_update_message = ""

    # -------------------------
    # SELLER LOGIN
    # -------------------------
    if not st.session_state.seller_logged_in:
        users = load_users()
        # Use the Users sheet as the source for seller names in the login dropdown.
        seller_names = sorted(
            {
                str(user.get("Username", "")).strip()
                for user in users
                if str(user.get("Username", "")).strip()
            },
            key=str.casefold
        )

        if seller_names:
            with st.form("seller_login_form"):

                seller_username = st.selectbox(
                    "Seller Name",
                    seller_names
                )

                seller_pin = st.text_input(
                    "Seller PIN",
                    type="password"
                )

                seller_login = st.form_submit_button(
                    "Seller Login"
                )

            if seller_login:
                selected_user = next(
                    (
                        user
                        for user in users
                        if str(user.get("Username", "")).strip().casefold()
                        == seller_username.casefold()
                    ),
                    None
                )
                stored_pin = (
                    str(selected_user.get("PIN", "")).strip()
                    if selected_user
                    else ""
                )

                # Sellers without an assigned PIN cannot log in until an admin sets one.
                if stored_pin and stored_pin == seller_pin.strip():
                    st.session_state.seller_logged_in = True
                    st.session_state.seller_name = seller_username
                    st.rerun()
                elif not stored_pin:
                    st.warning(
                        "A PIN has not been assigned to this seller yet. Please contact an administrator."
                    )
                else:
                    st.error("Invalid PIN")
        else:
            st.info("No sellers are registered yet.")

    # -------------------------
    # SELLER AREA
    # -------------------------
    if st.session_state.seller_logged_in:

        seller_name = (
            st.session_state.seller_name
        )

        col1, col2 = st.columns([6, 1])

        with col1:
            st.success(
                f"Logged in as {seller_name}"
            )

        with col2:
            if st.button(
                "Logout",
                key="seller_logout"
            ):
                st.session_state.seller_logged_in = False
                st.session_state.seller_name = ""
                st.rerun()

        all_records = get_records()

        # Only show and allow payment updates for the logged-in seller's tickets.
        seller_records = [
            row
            for row in all_records
            if row["Seller Name"].strip().lower()
            == seller_name.strip().lower()
        ]

        display_records = list(
            reversed(seller_records)
        )

        results = []

        for row in display_records:

            results.append(
                {
                    "Seller Name": row["Seller Name"],
                    "Ticket Holder": row["Name"],
                    "Ticket Number": row["Ticket Number"],
                    "Paid": row["Paid"]
                }
            )

        st.info(
            f"{len(results)} entries found."
        )

        st.dataframe(
            results,
            use_container_width=True
        )

        st.markdown("---")
        st.subheader(
            "Update Payment Status"
        )

        ticket_options = [
            f"{r['Ticket Number']} | {r['Name']} | {r['Seller Name']}"
            for r in display_records
        ]

        if ticket_options:

            with st.form(
                "seller_payment_update_form"
            ):

                selected_entry = st.selectbox(
                    "Select Entry",
                    ticket_options
                )

                new_status = st.selectbox(
                    "New Payment Status",
                    [
                        "Not Paid",
                        "Paid by revolut",
                        "Paid by BOI",
                        "Paid by Cash/Cheque"
                    ]
                )

                update_status = (
                    st.form_submit_button(
                        "Update Payment Status"
                    )
                )

            if (
                st.session_state.seller_update_message
            ):
                st.success(
                    st.session_state.seller_update_message
                )
                st.session_state.seller_update_message = ""

            if update_status:

                selected_ticket = (
                    selected_entry.split(" | ")[0]
                )

                row_number = None

                for idx, row in enumerate(
                    all_records,
                    start=2
                ):
                    if (
                        row["Ticket Number"]
                        == selected_ticket
                    ):
                        row_number = idx
                        break

                if row_number:

                    sheet.update_cell(
                        row_number,
                        5,
                        new_status
                    )

                    st.session_state.seller_update_message = (
                        f"✅ {selected_ticket} updated successfully to '{new_status}'"
                    )
                    get_records.clear()
                    st.rerun()

                else:
                    st.error(
                        "Ticket not found."
                    )

        else:
            st.info(
                "No entries found for this seller."
            )
# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Ballymore GAA Supporters Monthly Draw Ticket Entry System"
)
