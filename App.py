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

st.markdown(f"""
<style>
.logo-container {{
    position: fixed;
    top: 6px;
    left: 45px;
    z-index: 9999;
}}

.logo-container img {{
    height: 34px;
}}
</style>

<div class="logo-container">
    <img src="data:image/png;base64,{logo}">
</div>
""", unsafe_allow_html=True)
# -------------------------------
# LOAD GLOBAL CSS
# -------------------------------
with open(".streamlit/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# -------------------------------
# COMPACT CENTRED BANNER & UI CARDS
# -------------------------------
st.markdown("""
<div style="background:#FFD300;padding:6px 10px;border-radius:4px;margin-bottom:15px;text-align:center;">
    <span style="color:#000;font-weight:500;font-size:17px;font-family:'Georgia',serif;">
        🏐 Ballymore Supporters Draw - Sellers Online Entry 🏐
    </span>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# GOOGLE SHEETS CONNECTION & CACHE ALL RECORDS
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

client = get_client()

sheet = client.open_by_key(
    SHEET_ID
).worksheet("Ticket_Entries")

@st.cache_data(ttl=60)
def get_records():
    return sheet.get_all_records()

@st.cache_data(ttl=60)
def get_phone_numbers():
    return [
        str(x).strip().replace(" ", "")
        for x in sheet.col_values(4)[1:]
    ]

records = get_records()
ticket_count = len(records)
# --------------------------------------------------
# CSS STYLE For Buttons
# --------------------------------------------------
st.markdown("""
<style>

/* ===========================
   STANDARD BUTTONS
   =========================== */

.stButton > button {
    background-color: #FFD300 !important;
    color: #000000 !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: 1px solid #b8860b !important;
}

.stButton > button p {
    color: #000000 !important;
}

.stButton > button:hover {
    background-color: #ffea00 !important;
    color: #000000 !important;
    transform: translateY(-1px);
    transition: 0.2s;
}

/* ===========================
   FORM BUTTONS
   =========================== */

div[data-testid="stForm"] button {
    background-color: #FFD300 !important;
    color: #000000 !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: 1px solid #b8860b !important;
}

div[data-testid="stForm"] button p {
    color: #000000 !important;
}

div[data-testid="stForm"] button:hover {
    background-color: #ffea00 !important;
    transform: translateY(-1px);
    transition: 0.2s;
}

/* ===========================
   LINK BUTTONS
   =========================== */

[data-testid="stLinkButton"] a {
    background-color: #FFD300 !important;
    color: #000000 !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: 1px solid #b8860b !important;
}

[data-testid="stLinkButton"] a,
[data-testid="stLinkButton"] a * {
    color: #000000 !important;
    font-weight: bold !important;
}

[data-testid="stLinkButton"] a:hover {
    background-color: #ffea00 !important;
    color: #000000 !important;
    transform: translateY(-1px);
    transition: 0.2s;
}

/* ===========================
   METRICS
   =========================== */

[data-testid="stMetric"] {
    text-align: center;
    background-color: #FFF8CC;
    border: 1px solid #FFD700;
    border-radius: 10px;
    padding: 10px;
}

[data-testid="stMetric"] *,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: #000000 !important;
}

/* ===========================
   TABS
   =========================== */

/* All tabs */
.stTabs [data-baseweb="tab"] {
    min-height: 50px;
    padding: 0 20px;
    color: #555555 !important;
    font-weight: 500 !important;
    border-radius: 8px 8px 0 0;
}

/* Hover */
.stTabs [data-baseweb="tab"]:hover {
    color: #000000 !important;
}

/* ACTIVE TAB */
.stTabs [aria-selected="true"] {
    color: #B8860B !important;      /* Dark gold text */
    font-weight: 800 !important;
}

/* Active tab text */
.stTabs [aria-selected="true"] p {
    color: #B8860B !important;
    font-weight: 800 !important;
}

/* Yellow underline */
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #FFD300 !important;
    height: 4px !important;
}

</style>
""", unsafe_allow_html=True)
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
                get_phone_numbers.clear()
                st.session_state.reset_form = True
                st.session_state.show_success = True
                
                
                st.rerun()
# --------------------------------------------------
# VIEW ENTRIES
# --------------------------------------------------

    st.markdown("---")

    search_seller = st.text_input(
        "Enter Seller Name To View Entries",
        key="search_seller"
    )

    view_entries = st.button(
        "View My Entries",
        disabled=not st.session_state.seller_pin_ok
    )

    if view_entries:

        if not search_seller.strip():
            st.warning("Please enter a seller name.")
        else:

            records = get_records()

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
                    results, use_container_width=True
                )
            else:
                st.info("No entries found for that seller.")

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

    save_pin = st.text_input(
        "Enter 4‑digit PIN",
        type="password",
        max_chars=4
    )

    if save_pin == st.secrets["SAVE_PIN"]:
        st.session_state.save_pin_ok = True
        st.success("PIN accepted")
    elif save_pin == "":
        st.session_state.save_pin_ok = False
    else:
        st.session_state.save_pin_ok = False
        st.error("Incorrect PIN")

        st.markdown("---")

    last_year_sheet = client.open_by_key(SHEET_ID).worksheet(
        "Last_Year_Tickets"
    )

    show_sellers = st.button(
        "📋 Show Last Year's Tickets By Seller",
        disabled=not st.session_state.save_pin_ok
    )

    records = last_year_sheet.get_all_records()

    if not records:

        st.info(
            "No records found in Last Year's Tickets yet."
        )

    else:

        df = pd.DataFrame(records)

        df.columns = df.columns.str.strip()
            #if "show_sellers" doesn't exist:
        if "show_sellers" not in st.session_state:
            st.session_state.show_sellers = False

        if show_sellers:
            st.session_state.show_sellers = True

        if (st.session_state.show_sellers
            and st.session_state.save_pin_ok):

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

    admin_pin = st.text_input(
        "Admin PIN",
        type="password",
        key="dashboard_pin"
    )

    if admin_pin == st.secrets["ADMIN_PIN"]:

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

    elif admin_pin != "":
        st.error("Invalid PIN")

# --------------------------------------------------
# ADMIN VIEW
# --------------------------------------------------

with tab5:

    st.markdown("---")
    st.subheader("Admin Access")

    admin_pin = st.text_input(
        "Admin PIN",
        type="password"
    )

    if st.button("View Full Table"):

        if admin_pin == st.secrets["ADMIN_PIN"]:

            records = get_records()
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

            st.dataframe(results, use_container_width=True)


        else:
            st.error("Invalid PIN.")
# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Ballymore GAA Supporters Monthly Draw Ticket Entry System"
)

