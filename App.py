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
    page_title="Ballymore Draw Management",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
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

def get_seller_names(users):
    return sorted(
        {
            str(user.get("Username", "")).strip()
            for user in users
            if str(user.get("Username", "")).strip()
        },
        key=str.casefold
    )

def get_seller_pin(users, seller_name):
    selected_user = next(
        (
            user
            for user in users
            if str(user.get("Username", "")).strip().casefold()
            == seller_name.strip().casefold()
        ),
        None
    )
    return str(selected_user.get("PIN", "")).strip() if selected_user else ""

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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🎟 Ticket Entry",
        "📋 Last Year's Sales",
        "💳 Payment",
        "📊 Dashboard",
        "🔐 Admin",
        "📥 Download CSV"
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
        
        st.markdown("""
<div style="
    background: #fff8cc;
    color: #171717;
    padding: 1rem 1.25rem;
    border-radius: 10px;
    border: 2px solid #ffd300;
    text-align: center;
    font-weight: 500;
    font-size: 0.95rem;
">
    🔑 <strong>Enter Seller PIN</strong> to begin entering tickets.
</div>
""", unsafe_allow_html=True)
# --------------------------------------------------
# FORM
# --------------------------------------------------

    with st.form(
        "draw_entry_form",
        clear_on_submit=False
        ):

        st.markdown("#### 📝 Ticket Holder Information")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(
                "Full Name *",
                key="name",
                help="Name of the ticket holder"
            )
        with col2:
            phone = st.text_input(
                "Contact Number *",
                key="phone",
                help="10-digit mobile number (e.g., 0851234567)",
                placeholder="085..."
            )

        col1, col2 = st.columns(2)
        with col1:
            seller = st.text_input(
                "Seller Name *",
                key="seller",
                help="Your name as the ticket seller"
            )
        with col2:
            ticket = st.text_input(
                "Ticket Number *",
                key="ticket",
                help="E.g., T001 or WEB-001 (T prefix added automatically)",
                placeholder="001"
            )

        st.markdown("---")
        st.markdown("#### 💳 Payment Details")
        
        col1, col2 = st.columns([1.5, 1])
        with col1:
            paid = st.selectbox(
                "Payment Status *",
                [
                    "Not Paid",
                    "Paid by Revolut",
                    "Paid by BOI",
                    "Paid by Cash/Cheque",
                ],
                key="paid"
            )
        with col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

        comments = st.text_area(
            "Notes (Optional)",
            key="comments",
            max_chars=200,
            placeholder="Add any additional notes here...",
            height=80
        )

        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col2:
            submit = st.form_submit_button(
                "✅ Submit Entry",
                disabled=not st.session_state.seller_pin_ok,
                use_container_width=True
            )


#--------------------------------------------------
# New Section 
#--------------------------------------------------

    if st.session_state.show_success:
        st.success("✅ Entry submitted successfully! Ready to enter another ticket?")
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

        errors = []

        if not name:
            errors.append("• Please enter the ticket holder's name")
        
        if not seller:
            errors.append("• Please enter your name (seller)")
        
        if not ticket:
            errors.append("• Please enter the ticket number")
        
        if phone:
            if not phone.isdigit():
                errors.append("• Phone number must contain only digits")
            elif len(phone) != 10:
                errors.append("• Phone number must be exactly 10 digits")
        
        if errors:
            st.error("**Please fix the following errors:**\n\n" + "\n".join(errors))
        else:
            existing_phones = get_phone_numbers()

            phone_check = phone

            if phone_check and phone_check in existing_phones:
                st.error(f"⚠️ This phone number ({phone}) is already registered")
            else:
                if not ticket.upper().startswith("T"):
                    ticket = f"T{ticket}"

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
        st.subheader("📋 Your Submitted Tickets")

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
                "Select a seller to view their tickets",
                seller_names,
                key="entered_tickets_seller"
            )

            ticket_rows = [
                {
                    "🎟 Ticket #": str(row.get("Ticket Number", "")).strip(),
                    "Name": str(row.get("Name", "")).strip(),
                }
                for row in records
                if str(row.get("Seller Name", "")).strip().casefold()
                == selected_seller.casefold()
            ]

            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"**{len(ticket_rows)} tickets** entered by {selected_seller}")
            
            if ticket_rows:
                st.dataframe(
                    pd.DataFrame(ticket_rows),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No tickets found for this seller.")
        else:
            st.info("ℹ️ No seller entries yet. Submit your first ticket entry above!")

# --------------------------------------------------
# LAST YEAR'S SALES TAB
# --------------------------------------------------

with tab2:

    st.subheader("📋 Last Year's Tickets")

    if "save_pin_ok" not in st.session_state:
        st.session_state.save_pin_ok = False

    if not st.session_state.save_pin_ok:

        st.info("👤 Enter seller PIN to view last year's sales data")
        
        with st.form("last_year_login"):

            save_pin = st.text_input(
                "Enter 4-digit PIN",
                type="password",
                max_chars=4
            )

            pin_login = st.form_submit_button(
                "🔓 Login",
                use_container_width=True
            )

        if pin_login:

            if save_pin == st.secrets["SAVE_PIN"]:
                st.session_state.save_pin_ok = True
                st.rerun()
            else:
                st.error("❌ Incorrect PIN")

    if st.session_state.save_pin_ok:

        col1, col2 = st.columns([6,1])

        with col1:
            st.success("✅ Access Granted")

        with col2:
            if st.button(
                "🚪 Logout",
                key="last_year_logout"
            ):
                st.session_state.save_pin_ok = False
                st.rerun()

        st.markdown("---")

        records = get_last_year_records()

        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()

        seller_names = sorted(
            df["Seller"].dropna().unique()
        )

        seller = st.selectbox(
            "Select Seller",
            seller_names,
            key="last_year_seller"
        )

        filtered_df = df[
            df["Seller"] == seller
        ]

        col1, col2 = st.columns([2, 1])
        with col1:
            st.metric(
                "📊 Tickets Last Year",
                len(filtered_df)
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )
# --------------------------------------------------
# REVOLUT PAYMENT TAB
# --------------------------------------------------

with tab3:

    st.subheader("💳 Payment Methods")

    st.markdown("""
Choose your preferred payment method below. All payments help support Ballymore GAA club activities.
""")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📱 Revolut Payment")
        st.markdown("""
Quick and easy payment through the Revolut app.
        """)
        st.link_button(
            "💳 Pay with Revolut",
            st.secrets["REVOLUT_LINK"],
            use_container_width=True
        )
        
        st.markdown("**Scan QR Code:**")
        st.image(
            "revolut_qr.png",
            caption="Open Revolut and scan this code",
            use_container_width=True
        )

    with col2:
        st.markdown("### 🏦 Bank Transfer (BOI)")
        st.markdown("""
Bank of Ireland transfer. Please include your name as a reference.
        """)
        
        st.markdown("**Bank Details:**")
        
        detail_col1, detail_col2 = st.columns([1, 2])
        with detail_col1:
            st.markdown("**Club Name**")
            st.markdown("**IBAN**")
            st.markdown("**BIC**")
        with detail_col2:
            st.code("BALLYMORE GAA")
            st.code("IE71BOFI90177371264687")
            st.code("BOFIIE2DXXX")
        
        st.info("✏️ **Reference:** Please include your name as the payment reference")

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
with tab4:

    st.subheader("📊 Sales Dashboard")

    st.markdown("""
Enter seller PIN to view ticket sales and performance metrics.
""")

    save_pin = st.text_input(
        "Enter PIN to View Dashboard",
        type="password",
        max_chars=4,
        key="dashboard_pin"
    )

    if save_pin == st.secrets["SAVE_PIN"]:

        records = get_records()

        if not records:
            st.info("ℹ️ No data available yet.")
            st.stop()

        df = pd.DataFrame(records)

        st.markdown("---")
        st.markdown("### 📈 Key Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "🎟 Total Entries",
                len(df)
            )

        with col2:
            st.metric(
                "👥 Unique Sellers",
                df["Seller Name"].nunique()
            )

        paid_count = len(df[df["Paid"] != "Not Paid"]) if "Paid" in df.columns else 0
        with col3:
            st.metric(
                "✅ Paid Entries",
                paid_count
            )

        pending_count = len(df[df["Paid"] == "Not Paid"]) if "Paid" in df.columns else 0
        with col4:
            st.metric(
                "⏳ Pending Payment",
                pending_count
            )

        st.markdown("---")

        # Payment breakdown
        if "Paid" in df.columns:
            payment_counts = (
                df["Paid"]
                .fillna("Unknown")
                .value_counts()
            )
            
            st.markdown("### 💳 Payment Methods Breakdown")
            st.bar_chart(payment_counts)

        st.markdown("---")

        # Seller leaderboard
        st.markdown("### 🏆 Top Sellers")

        seller_counts = (
            df["Seller Name"]
            .fillna("Unknown")
            .value_counts()
        )

        st.bar_chart(seller_counts.head(10))

    elif save_pin != "":
        st.error("❌ Invalid PIN")

# --------------------------------------------------
# ADMIN VIEW
# --------------------------------------------------
with tab5:

    st.markdown("---")
    st.subheader("🔐 Admin Access")

    if "admin_pin_ok" not in st.session_state:
        st.session_state.admin_pin_ok = False

    if "admin_update_message" not in st.session_state:
        st.session_state.admin_update_message = ""

    if "admin_payment_update_message" not in st.session_state:
        st.session_state.admin_payment_update_message = ""

    if not st.session_state.admin_pin_ok:

        st.info("👤 Administrator credentials required")

        with st.form("admin_login_form"):

            admin_pin = st.text_input(
                "Admin PIN",
                type="password"
            )

            admin_login = st.form_submit_button(
                "🔓 Login",
                use_container_width=True
            )

        if admin_login:

            if admin_pin == st.secrets["ADMIN_PIN"]:
                st.session_state.admin_pin_ok = True
                st.rerun()
            else:
                st.error("❌ Invalid PIN")

    if st.session_state.admin_pin_ok:

        col1, col2 = st.columns([6, 1])

        with col1:
            st.success("✅ ADMIN LOGGED IN")

        with col2:
            if st.button(
                "🚪 Logout",
                key="admin_logout"
            ):
                st.session_state.admin_pin_ok = False
                st.rerun()

        st.markdown("---")
        st.subheader("👤 Manage Seller PINs")

        users = load_users()
        user_table = [
            {
                "Username": str(user.get("Username", "")).strip(),
                "PIN": str(user.get("PIN", "")).strip()
            }
            for user in users
        ]
        
        if user_table:
            st.dataframe(
                pd.DataFrame(user_table, columns=["Username", "PIN"]),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("ℹ️ No users registered yet.")

        user_names = [
            user["Username"]
            for user in user_table
            if user["Username"]
        ]

        if user_names:
            st.markdown("---")
            st.markdown("### 🔑 Set or Reset PIN")
            
            with st.form("admin_user_pin_form"):
                selected_user = st.selectbox(
                    "Select user",
                    user_names
                )
                new_user_pin = st.text_input(
                    "New 4-digit PIN",
                    type="password",
                    max_chars=4
                ) or ""
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    update_user_pin = st.form_submit_button(
                        "💾 Save PIN",
                        use_container_width=True
                    )

            if update_user_pin:
                if selected_user not in user_names:
                    st.error("Select a valid user.")
                elif (
                    len(new_user_pin) != 4
                    or any(digit not in "0123456789" for digit in new_user_pin)
                ):
                    st.error("Enter a PIN containing exactly 4 digits.")
                else:
                    user_row = next(
                        (
                            row_number
                            for row_number, user in enumerate(users, start=2)
                            if str(user.get("Username", "")).strip().casefold()
                            == selected_user.casefold()
                        ),
                        None
                    )

                    if user_row is None:
                        st.error("The selected user was not found in the Users sheet.")
                    else:
                        users_sheet.update_cell(user_row, 2, new_user_pin)
                        load_users.clear()
                        st.session_state.admin_update_message = (
                            f"✅ PIN updated for {selected_user}."
                        )
                        st.rerun()
        else:
            st.info("ℹ️ No users are listed in the Users sheet yet.")

        if st.session_state.admin_update_message:
            st.success(st.session_state.admin_update_message)
            st.session_state.admin_update_message = ""

        st.markdown("---")
        st.subheader("📋 All Ticket Entries")

        records = get_records()

        display_records = list(reversed(records))

        results = []

        for row in display_records:
            results.append(
                {
                    "👤 Seller": row["Seller Name"],
                    "🎟 Ticket #": row["Ticket Number"],
                    "📝 Name": row["Name"],
                    "💳 Status": row["Paid"]
                }
            )

        st.info(f"**Total:** {len(results)} entries found")

        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True
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

        if st.session_state.admin_payment_update_message:
            st.success(
                st.session_state.admin_payment_update_message
            )
            st.session_state.admin_payment_update_message = ""

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

                st.session_state.admin_payment_update_message = (
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
        seller_names = get_seller_names(users)

        if seller_names:
            with st.form("seller_login_form"):

                seller_username = st.selectbox(
                    "Seller Name",
                    seller_names
                )

                seller_pin = st.text_input(
                    "Seller - Unique PIN",
                    type="password"
                )

                seller_login = st.form_submit_button(
                    "Seller Login"
                )

            if seller_login:
                stored_pin = get_seller_pin(users, seller_username)

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
            f"{r['Ticket Number']} | {r['Name']}"
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

with tab6:

    st.subheader("📥 Download Ticket Entries CSV")

    if not st.session_state.seller_logged_in:
        users = load_users()
        seller_names = get_seller_names(users)

        if seller_names:
            with st.form("download_seller_login_form"):
                download_seller = st.selectbox(
                    "Seller Name",
                    seller_names,
                    key="download_seller_name"
                )
                download_pin = st.text_input(
                    "Seller - Unique PIN",
                    type="password",
                    key="download_seller_pin"
                )
                download_login = st.form_submit_button("Seller Login")

            if download_login:
                stored_pin = get_seller_pin(users, download_seller)
                if stored_pin and stored_pin == download_pin.strip():
                    st.session_state.seller_logged_in = True
                    st.session_state.seller_name = download_seller
                    st.rerun()
                elif not stored_pin:
                    st.warning(
                        "A PIN has not been assigned to this seller yet. Please contact an administrator."
                    )
                else:
                    st.error("Invalid PIN")
        else:
            st.info("No sellers are registered yet.")

    if st.session_state.seller_logged_in:
        st.success(f"Logged in as {st.session_state.seller_name}")
        if st.button("Logout", key="download_seller_logout"):
            st.session_state.seller_logged_in = False
            st.session_state.seller_name = ""
            st.rerun()

        st.caption(
            "The download contains all ticket entries, name, ticket number and seller. "
            "Data is cached for up to 60 seconds; refresh to get the latest entries."
        )

        if st.button("🔄 Refresh ticket entries", key="refresh_download_entries"):
            get_records.clear()
            st.rerun()

        download_records = get_records()
        if download_records:
            download_rows = [
                {
                    "Name and Ticket Number": " ".join(
                        part for part in (
                            str(row["Name"]).strip(),
                            str(row["Ticket Number"]).strip(),
                        ) if part
                    ),
                    "Seller": str(row["Seller Name"]).strip(),
                }
                for row in download_records
            ]
            download_csv = pd.DataFrame(download_rows).to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "📥 Download ticket entries CSV",
                data=download_csv,
                file_name="ticket_entries.csv",
                mime="text/csv",
                on_click="ignore",
            )
        else:
            st.info("No ticket entries are available to download.")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Ballymore GAA Supporters Monthly Draw Ticket Entry System"
)
