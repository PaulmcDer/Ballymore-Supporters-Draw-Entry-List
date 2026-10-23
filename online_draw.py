import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import stripe
#from email.message import EmailMessage
#import smtplib

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Ballymore Draw Online",
    page_icon="🎟️",
    layout="centered"
)
SHEET_ID = "1umG0zNs4Uz9IqfZXPXEeAgfSWoRTzDDsEwlSRC-3PnM"
EMAIL_ENABLED = False
APP_URL = st.secrets["APP_URL"]

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
processed_sheet = client.open_by_key(SHEET_ID).worksheet("Processed_Stripe_Sessions")

records = sheet.get_all_records()
ticket_count = len(records)

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

# --------------------------------------------------
# EMAIL CONFIRMATION
# --------------------------------------------------

def send_confirmation_email(
    recipient,
    full_name,
    allocated_tickets
):

    msg = EmailMessage()

    msg["Subject"] = (
        "Ballymore Draw Ticket Confirmation"
    )

    msg["From"] = st.secrets["EMAIL_USER"]

    msg["To"] = recipient

    ticket_list = "\n".join(
        allocated_tickets
    )

    msg.set_content(
        f"""
Thank you {full_name} for supporting Ballymore GFC.

Your ticket numbers are:

{ticket_list}

Good luck in the draw.

Ballymore Supporters Draw
"""
    )

    try:

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
            timeout=10
        ) as smtp:
                
            st.write("SMTP connection established")

            smtp.ehlo()

            smtp.starttls()

            smtp.ehlo()

            smtp.login(
                st.secrets["EMAIL_USER"],
                st.secrets["EMAIL_PASSWORD"]
            )

            st.write("Logged in. Sending email...")

            smtp.send_message(msg)

        st.success(
            "Email sent successfully"
        )

    except Exception as e:

        st.error(
            f"Email failed: {e}"
        )
# --------------------------------------------------
# STRIPE Sucess 
# --------------------------------------------------

success = st.query_params.get("success")
session_id = st.query_params.get("session_id")
cancelled = st.query_params.get("cancelled")

if cancelled == "true":

    st.warning(
        "Payment was cancelled. No tickets have been allocated."
    )

if success == "true":

    session = stripe.checkout.Session.retrieve(
        session_id
    )

    if session.payment_status != "paid":

        st.error(
            "Payment has not been completed."
        )
        st.stop()
    #This prevents duplicate entries on refresh 
    processed_ids = processed_sheet.col_values(1)

    if session_id in processed_ids:

        st.warning(
            "This payment has already been processed."
        )

        st.stop()
    quantity = int(
        session.metadata["quantity"]
    )

    # Allocate tickets
    
    # Show confirmation
    
    # -----------------------------------------
    # EXTRACT METADATA
    # -----------------------------------------
    # Write Ticket_Entries
    
    full_name = session.metadata["full_name"]
    mobile = session.metadata["mobile"]
    email = session.metadata["email"]

    quantity = int(
        session.metadata["quantity"]
    )

    # -----------------------------------------
    # FIND NEXT WEB NUMBER
    # -----------------------------------------

    records = sheet.get_all_records()

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

    next_ticket = max(
        web_numbers,
        default=0
    ) + 1

    # -----------------------------------------
    # CREATE TICKETS
    # -----------------------------------------

    allocated_tickets = []

    for i in range(quantity):

        ticket_number = (
            f"WEB-{next_ticket + i:03d}"
        )

        allocated_tickets.append(
            ticket_number
        )

    # -----------------------------------------
    # DISPLAY TICKETS
    # -----------------------------------------
    st.success(
    "Payment Successful ✅"
    )

    st.write(
    f"Thank you {full_name} for supporting Ballymore GFC."
    )

    st.subheader(
        "Your Ticket Numbers"
    )

    for ticket in allocated_tickets:

        st.code(ticket)

    st.info(
        "Your tickets have been recorded and entered into the Ballymore Supporters Draw."
    )

    # -----------------------------------------
    # WRITE TICKETS TO GOOGLE SHEET
    # -----------------------------------------
    timestamp = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    for ticket in allocated_tickets:

        sheet.append_row(
            [
                full_name,          # Name
                "WEB",              # Seller Name
                ticket,             # Ticket Number
                mobile,             # Phone Number
                "Paid",             # Paid
                timestamp,          # Date Submitted
                "Online Purchase"   # Comments
            ]
        )

# -----------------------------------------
# EMAIL TEMPORARILY DISABLED
# -----------------------------------------

# send_confirmation_email(
#     email,
#     full_name,
#     allocated_tickets
# )

# -----------------------------------------
# MARK SESSION AS PROCESSED
# -----------------------------------------

processed_sheet.append_row(
    [session_id]
)
# --------------------------------------------------
# STRIPE CHECKOUT SESSION
# --------------------------------------------------

def create_checkout_session(
    amount_eur,
    full_name,
    mobile,
    email,
    quantity
):

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "Ballymore Draw Tickets"
                    },
                    "unit_amount": amount_eur * 100,
                },
                "quantity": 1,
            }
        ],
        customer_email=email,
        metadata={
            "full_name": full_name,
            "mobile": mobile,
            "email": email,
            "quantity": str(quantity)
        },
        success_url=(
            f"{APP_URL}"
            "?success=true"
            "&session_id={CHECKOUT_SESSION_ID}"
        ),

        cancel_url=(
            f"{APP_URL}?cancelled=true"
        ),

    )
    return session.url

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
#--------------------------------------------------
#Ticket Calculation
#--------------------------------------------------
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

st.write(
    f"🎟 Reserved Ticket Numbers: {len(estimated_tickets)}"
)

# --------------------------------------------------
# PURCHASE FORM
# --------------------------------------------------

with st.form(
    "online_purchase_form",
    clear_on_submit=False
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

    col1, col2 = st.columns([1.3, 1])

    with col1:

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

    with col2:

        st.markdown("### Confirm")

        accept_terms = st.checkbox(
            "I confirm I wish to purchase these tickets"
        )

        submit = st.form_submit_button(
            "💳 Continue To Checkout"
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
            "Details accepted ✅"
        )

        st.markdown("### Payment Summary")

        st.write(f"👤 {full_name}")
        st.write(f"📱 {mobile}")
        st.write(f"📧 {email}")
        st.write(f"🎟️ {quantity} ticket(s)")
        st.write(f"💰 Total Due: €{total_cost}")

        st.markdown("---")

        st.session_state["buyer_name"] = full_name
        st.session_state["buyer_mobile"] = mobile
        st.session_state["buyer_email"] = email
        st.session_state["buyer_quantity"] = quantity

        checkout_url = create_checkout_session(
            total_cost,
            full_name,
            mobile,
            email,
            quantity
        )

        st.link_button(
            f"💳 Continue to Stripe (€{total_cost})",
            checkout_url
        )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")

st.caption(
    "Ballymore Supporters Draw Online"
)
