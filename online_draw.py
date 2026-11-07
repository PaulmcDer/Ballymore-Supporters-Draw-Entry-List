# ==================================================
# IMPORTS
# ==================================================
#1. Imports
#2. Settings / Constants
#3. Connections (Google / Stripe)
#4. Functions
#5. Load Data
#6. Process Payment Return
#7. Display UI
#8. Validate Form
#9. Redirect to Stripe

import streamlit as st
import stripe
import gspread
import smtplib
import base64
import html

from datetime import datetime
from email.message import EmailMessage
from google.oauth2.service_account import Credentials
from gspread.utils import ValueInputOption

# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(
    page_title="Ballymore Draw Online",
    page_icon="logo.png",
    layout="centered"
)

# ==================================================
# APP SETTINGS / CONSTANTS
# ==================================================

SHEET_ID = "1umG0zNs4Uz9IqfZXPXEeAgfSWoRTzDDsEwlSRC-3PnM"
DEBUG_EMAIL = False
APP_URL = st.secrets["APP_URL"]
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

# ==================================================
# CUSTOM STYLES
# ==================================================

with open(".streamlit/online_draw.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

with open("logo.png", "rb") as f:
    logo = base64.b64encode(f.read()).decode("ascii")

st.markdown(f"""
<header class="draw-hero">
    <img src="data:image/png;base64,{logo}" alt="Ballymore GAA crest">
    <div>
        <h1>Support Ballymore GAA</h1>
        <p>12 draws a year, 12 chances to win per entry..</p>
    </div>
</header>
<section class="draw-offer">
    <h3>Your entry for the year</h3>
    <p><strong>€100 per ticket</strong> &nbsp;·&nbsp; Monthly prizes: €1,000, €100 and €100</p>
    <p>Choose your tickets and holder names below. Payment is securely completed with Stripe.</p>
</section>
""", unsafe_allow_html=True)

# --------------------------------------------------
# GOOGLE SHEETS CONNECTION
# --------------------------------------------------

@st.cache_resource
def get_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)

    return (
        spreadsheet.worksheet("Ticket_Entries"),
        spreadsheet.worksheet("Processed_Stripe_Sessions")
    )


sheet, processed_sheet = get_sheets()

# ==================================================
# GOOGLE SHEET FUNCTIONS
# ==================================================

@st.cache_data(ttl=60)
def get_ticket_numbers():
    return sheet.col_values(3)[1:]

# ==================================================
# LOAD DATA
# ==================================================

ticket_numbers = get_ticket_numbers()
ticket_count = len(ticket_numbers)

# ==================================================
# EMAIL FUNCTIONS
# ==================================================

def send_confirmation_email(
    recipient,
    full_name,
    allocated_tickets,
    ticket_names
):

    msg = EmailMessage()

    msg["Subject"] = (
        "Ballymore Draw Ticket Confirmation"
    )

    msg["From"] = st.secrets["EMAIL_USER"]

    msg["To"] = recipient

    ticket_list = "\n".join(
        f"{ticket} — {name}"
        for ticket, name in zip(allocated_tickets, ticket_names)
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

            if DEBUG_EMAIL:
                st.write("SMTP connection established")
                st.write("Logged in. Sending email...")

            smtp.ehlo()

            smtp.starttls()

            smtp.ehlo()

            smtp.login(
                st.secrets["EMAIL_USER"],
                st.secrets["EMAIL_PASSWORD"]
            )

            smtp.send_message(msg)

        st.success(
            "Email sent successfully"
        )

    except Exception as e:

        st.error(
            f"Email failed: {e}"
        )
# ==================================================
# STRIPE FUNCTIONS & STRIPE SUCCESS
# ==================================================

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

        st.query_params.clear()
        st.rerun()

        st.stop()
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
    ticket_names = session.metadata["ticket_names"].split("|")

    get_ticket_numbers.clear()
    ticket_numbers = get_ticket_numbers()

    # -----------------------------------------
    # HELPER FUNCTIONS
    # -----------------------------------------

    web_numbers = []

    for ticket in ticket_numbers:
        ticket = str(ticket)

        if ticket.startswith("WEB-"):
            try:
                web_numbers.append(
                    int(ticket.removeprefix("WEB-"))
                )
            except ValueError:
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
    st.success("Payment successful")
    st.write(f"Thank you, {full_name}, for supporting Ballymore GFC.")
    st.subheader("Your draw entries")

    for i, ticket in enumerate(allocated_tickets):
        st.markdown(
            f'<div class="ticket-card"><strong>{html.escape(ticket)}</strong>'
            f'<span>{html.escape(ticket_names[i])}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="draw-confirmation">
        <strong>Your tickets are in the draw.</strong><br>
        Please check the email address you provided for a confirmation.
    </div>
    """, unsafe_allow_html=True)


    # -----------------------------------------
    # WRITE TICKETS TO GOOGLE SHEET
    # -----------------------------------------
    timestamp = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    ticket_rows = [
        [
            ticket_names[i],    # Name for this ticket
            "WEB",              # Seller Name
            ticket,             # Ticket Number
            mobile,             # Phone Number
            "Paid",             # Paid7
            timestamp,          # Date Submitted
            "Online Purchase"   # Comments
        ]
        for i, ticket in enumerate(allocated_tickets)
    ]
    sheet.append_rows(
        ticket_rows,
        value_input_option=ValueInputOption.raw
    )
    get_ticket_numbers.clear()
    ticket_numbers = get_ticket_numbers()
    send_confirmation_email(
        email,
        full_name,
        allocated_tickets,
        ticket_names
    )

# -----------------------------------------
# MARK SESSION AS PROCESSED
# -----------------------------------------

    processed_sheet.append_row(
    [session_id]
    )
    get_ticket_numbers.clear()
# --------------------------------------------------
# STRIPE CHECKOUT SESSION
# --------------------------------------------------

def create_checkout_session(
    amount_eur,
    full_name,
    mobile,
    email,
    quantity,
    ticket_names
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
            "quantity": str(quantity),
            "ticket_names": "|".join(ticket_names)

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
# SIDEBAR CONTENT
# --------------------------------------------------
with st.sidebar:

    with st.container(horizontal_alignment="center"):
        st.image("logo.png", width=56, alt="Ballymore GAA crest")

    st.markdown(
        "<h3 style='text-align:center;'>Ballymore GAA Draw Information</h3>",
        unsafe_allow_html=True
    )
    st.markdown("""
    <div class="draw-offer">
        <h3>About the draw</h3>
        <p>€100 per ticket</p>
        <p>One ticket enters you in all 12 monthly draws for the year</p>
        <p>Monthly prizes: €1,000, €100 and €100</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("Questions? Contact ballymoredraw@gmail.com")
    st.markdown("---")

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown(
    '<h2 class="draw-section-title">Choose your tickets</h2>'
    '<p class="draw-section-caption">Select a quantity to see your total.</p>',
    unsafe_allow_html=True
)

#--------------------------------------------------
#Ticket Calculation
#--------------------------------------------------
quantity = st.selectbox(
    "Number of Tickets",
    [1, 2, 3, 4, 5]
)

total_cost = quantity * 100

st.markdown(
    f'<div class="price-summary"><span>{quantity} ticket(s) selected</span>'
    f'<strong>Total €{total_cost:,}</strong></div>',
    unsafe_allow_html=True
)

# ==================================================
# TICKET HOLDER NAMES
# ==================================================

st.markdown("#### Ticket holder names")
use_primary_name = st.checkbox(
    "Use primary name for all tickets",
    value=True
)

# ==================================================
# PURCHASE FORM
# ==================================================
        
with st.form(
    "online_purchase_form",
    clear_on_submit=False
):
    st.markdown("#### Your details")
    full_name = st.text_input(
        "Full Name"
    )

    mobile = st.text_input(
        "Mobile Number"
    )

    email = st.text_input(
    "Email Address"
    )

    ticket_names = []

    if use_primary_name:

        ticket_names = [full_name] * quantity

    else:

        for i in range(quantity):

            ticket_name = st.text_input(
                f"Name for Ticket {i+1}",
                key=f"ticket_name_{i}"
            )

            ticket_names.append(ticket_name)
    
    col1, col2 = st.columns([1.3, 1])

    with col1:
        with st.container(key="purchase-summary"):
            st.markdown("### Purchase summary")
            st.write(f"Tickets: **{quantity}**")
            st.write(f"Total: **€{total_cost:,}**")
            st.caption(
                "Ticket numbers are assigned after successful payment."
            )

    with col2:
        with st.container(key="purchase-confirm"):
            st.markdown("### Ready to enter?")
            st.caption("Payment is securely processed by Stripe.")
            accept_terms = st.checkbox(
                "I confirm I wish to purchase these tickets"
            )

            submit = st.form_submit_button(
                "Continue to secure checkout"
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

        # Validate ticket names
        if not use_primary_name:
            for i, name in enumerate(ticket_names):
                if not name.strip():
                    st.error(f"Please enter a name for Ticket {i+1}.")
                    st.stop()

        st.success(
        "Details accepted ✅")

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
            quantity,
            ticket_names #new
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
