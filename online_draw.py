import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Ballymore Draw Online",
    page_icon="🎟️",
    layout="centered"
)

# --------------------------------------------------
# CSS
# --------------------------------------------------

st.markdown("""
<style>

/* Buttons */
.stButton > button,
div[data-testid="stForm"] button {
    background-color: #FFD700 !important;
    color: black !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: 1px solid #b8860b !important;
}

.stButton > button *,
div[data-testid="stForm"] button * {
    color: black !important;
}

/* Centre metric */
[data-testid="stMetric"] {
    text-align: center;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

SHEET_ID = "1umG0zNs4Uz9IqfZXPXEeAgfSWoRTzDDsEwlSRC-3PnM"

st.set_page_config(
    page_title="Supporters Monthly Draw Tickets",
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

sheet = client.open_by_key(SHEET_ID).worksheet("Ticket_Entries")

records = sheet.get_all_records()
ticket_count = len(records)

# --------------------------------------------------
# FIND NEXT WEB TICKET NUMBER
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
) + 1

online_ticket_count = len(web_numbers)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

col1, col2, col3 = st.columns([1, 0.7, 1])

with col2:
    st.image(
        "logo.png",
        width=140
    )

st.markdown(
    """
    <h2 style='text-align:center;'>
    🏐️ Ballymore Supporters Draw  🏐
    </h2>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align:center; font-size:14px;'>
    <i>
    Complete your details below to purchase Draw Tickets.
    </i>
    </p>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Tickets Entered",
        ticket_count
    )

with col2:
    st.metric(
        "Online Tickets",
        online_ticket_count
    )

with col3:
    st.metric(
        "Next Ticket",
        f"WEB-{next_web_ticket:03d}"
    )

st.markdown("---")

# --------------------------------------------------
# DRAW DETAILS
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:

    st.markdown("""
    ### 🎟️ Draw Details

    🎟️ **1 Ticket €100**

    ✅ Entry into 12 monthly draws

    🥇 **1st Prize:** €1,000

    🥈 **2nd Prize:** €100

    🥉 **3rd Prize:** €100
    """)

with col2:

    st.markdown("""
    ### ✅ Benefits

    ✅ Secure online purchase

    ✅ Instant ticket allocation

    ✅ Up to 5 tickets per transaction

    ✅ Supports Ballymore GFC

    ✅ 12 chances to win each year
    """)
# --------------------------------------------------
# PURCHASE FORM
# --------------------------------------------------

with st.form(
    "online_purchase_form",
    clear_on_submit=True
):

    full_name = st.text_input(
        "Full Name"
    )

    mobile = st.text_input(
        "Mobile Number"
    )

    email = st.text_input(
        "Email Address"
    )

    quantity = st.selectbox(
        "Number of Tickets",
        [1, 2, 3, 4, 5]
    )

    total_cost = quantity * 100

    st.markdown(
        f"**Total Cost: €{total_cost:,}**"
    )

    estimated_tickets = []

    for i in range(quantity):

        estimated_tickets.append(
            f"WEB-{next_web_ticket + i:03d}"
        )

    st.info(
        "Estimated Ticket Numbers: "
        + ", ".join(
            estimated_tickets
        )
    )

    st.markdown("### Purchase Summary")

    st.write(
        f"🎟️ Tickets: {quantity}"
    )

    st.write(
        f"💰 Total Cost: €{total_cost}"
    )

    st.write(
        "🔢 Estimated Numbers:"
    )

    for ticket in estimated_tickets:
        st.write(ticket)

    accept_terms = st.checkbox(
        "I confirm I wish to purchase the selected tickets."
    )

    submit = st.form_submit_button(
        "💳 Continue To Payment"
    )
# --------------------------------------------------
# PLACEHOLDER PAYMENT LOGIC
# --------------------------------------------------

if submit:


    if not accept_terms:

        st.error(
            "Please confirm the purchase first."
        )

    elif not full_name.strip():

        st.error(
            "Please enter your full name."
        )

        st.error(
            "Please enter your full name."
        )

    elif not mobile.strip():

        st.error(
            "Please enter your mobile number."
        )

    elif not email.strip():

        st.error(
            "Please enter your email address."
        )

    else:

        st.success(
            "Payment Successful ✅"
        )

        st.subheader(
            "Allocated Ticket Numbers"
        )

        for ticket in estimated_tickets:

            st.write(ticket)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Ballymore Supporters Draw Online"
)
