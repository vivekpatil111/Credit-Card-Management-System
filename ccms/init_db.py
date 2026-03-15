#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CCMS – SQLite data‑generator (100 rows per table)
------------------------------------------------
*  Creates the database file  :  ccms.db
*  Populates every table with 100 rows of random but consistent data.
*  All FK relationships are honoured.
*  Uses the same “pools” (names, cities, merchants …) you supplied.
*  After the script finishes you can run the 40 analytical queries that
   you already have for the SQL‑Server version – they work on SQLite as well
   (just change the connection string).

Author : ChatGPT  (2024‑06)
"""

import sqlite3, os, random
from datetime import date, timedelta

# ----------------------------------------------------------------------
#  CONFIGURATION
# ----------------------------------------------------------------------
DB_NAME      = "ccms.db"
RNG_SEED     = 42                # same seed → reproducible data
random.seed(RNG_SEED)

# ----------------------------------------------------------------------
#  Helper functions – random date / time
# ----------------------------------------------------------------------
def rdate(start: str = "2020-01-01", end: str = "2026-03-01") -> str:
    """Return a random ISO‑date between *start* and *end* (inclusive)."""
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    delta = (e - s).days
    return str(s + timedelta(days=random.randint(0, delta)))

def rtime() -> str:
    """Return a random HH:MM:SS (seconds are always 00)."""
    return f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:00"

# ----------------------------------------------------------------------
#  Data pools (the same lists you already defined)
# ----------------------------------------------------------------------
FNAMES_M = ["Rahul","Amit","Vikram","Rohit","Suresh","Deepak","Manish","Rajesh","Nikhil","Arun",
            "Sachin","Vikas","Sanjay","Ravi","Ajay","Prakash","Mahesh","Dinesh","Ramesh","Naresh",
            "Pradeep","Santosh","Abhishek","Akash","Vishal","Gaurav","Pankaj","Sumit","Ankit","Vivek",
            "Arjun","Karan","Rohan","Tarun","Varun","Hardik","Nitin","Tushar","Mayur","Shubham"]
FNAMES_F = ["Priya","Sneha","Neha","Anjali","Kavita","Pooja","Sunita","Rekha","Anita","Meena",
            "Shalini","Divya","Nisha","Ritu","Seema","Geeta","Asha","Usha","Lata","Mona",
            "Swati","Preeti","Pallavi","Shweta","Archana","Madhuri","Smita","Komal","Jyoti","Bharti",
            "Aishwarya","Shruti","Sonali","Yamini","Radhika","Sapna","Vandana","Mamta","Bindu","Sudha"]
LNAMES   = ["Sharma","Patel","Singh","Gupta","Joshi","Verma","Mehta","Desai","Nair","Rao",
            "Kumar","Mishra","Tiwari","Agarwal","Pillai","Shah","Iyer","Reddy","Pandey","Dubey",
            "Bhatia","Malhotra","Saxena","Srivastava","Chaudhary","Kapoor","Khanna","Bansal","Goel","Arora",
            "Chauhan","Rastogi","Bhatt","Tripathi","Shukla","Yadav","Patil","Kulkarni","More","Jadhav"]
CITIES   = ["Mumbai","Delhi","Bangalore","Hyderabad","Chennai","Kolkata","Pune","Ahmedabad","Jaipur","Lucknow",
            "Surat","Nagpur","Indore","Bhopal","Patna","Vadodara","Ludhiana","Agra","Nashik","Thane",
            "Meerut","Rajkot","Varanasi","Amritsar","Allahabad","Howrah","Coimbatore","Guwahati","Chandigarh","Kochi"]
AREAS    = ["Andheri West","Borivali East","Powai","Dadar","Kandivali West","Goregaon East","Malad West",
            "Chembur","Vashi","Thane West","Bandra","Juhu","Santacruz","Ghatkopar","Kurla","Mulund",
            "MG Road","Koramangala","Indiranagar","Whitefield","HSR Layout","JP Nagar","Marathahalli"]
BANKS    = ["HDFC Bank","State Bank of India","ICICI Bank","Axis Bank","Kotak Mahindra Bank",
            "Punjab National Bank","Bank of Baroda","Canara Bank","Union Bank of India","Bank of India",
            "IndusInd Bank","Yes Bank","Federal Bank","South Indian Bank","Karnataka Bank",
            "IDBI Bank","UCO Bank","Syndicate Bank","Vijaya Bank","Allahabad Bank"]
IFSC_PFX = ["HDFC","SBIN","ICIC","UTIB","KKBK","PUNB","BARB","CNRB","UBIN","BKID",
            "INDB","YESB","FDRL","SIBL","KARB","IBKL","UCBA","SYNB","VIJB","ALLA"]
MERCHANTS= ["Amazon India","Flipkart","Swiggy","Zomato","BigBazaar","DMart","Myntra","Nykaa",
            "BookMyShow","Croma Electronics","Reliance Digital","Kalyan Jewellers","Taj Restaurant",
            "McDonald's","KFC","Domino's Pizza","Starbucks","HDFC ATM","SBI ATM","ICICI ATM",
            "MakeMyTrip","Yatra","IRCTC","Ola","Uber","Rapido","PhonePe","Paytm","Google Pay",
            "Tanishq","Malabar Gold","Lifestyle","Westside","Pantaloons","Central Mall",
            "Apollo Pharmacy","MedPlus","Practo","1mg","Lenskart","Boat","OnePlus Store",
            "Bata","Nike","Adidas","H&M","Zara","Foreign POS - Dubai","Foreign POS - Singapore",
            "Unknown Merchant","Suspicious Vendor","Night Club POS"]
TXN_TYPES= ["Online","POS","ATM","Food","Dining","Travel","Shopping","Entertainment","Medical","Fuel"]
CARD_TYPES=["Visa Gold","Visa Classic","Visa Platinum","Visa Signature","Mastercard Gold",
            "Mastercard Classic","Mastercard Platinum","Mastercard World","Amex Gold","Amex Classic"]
DEPARTMENTS=["Fraud & Security","Customer Support","Billing","Card Operations","Risk Management",
             "Compliance","IT Support","Collections","Accounts","HR","Marketing","Legal"]
EMP_ROLES  =["Fraud Analyst","Support Agent","Billing Executive","Card Executive","Risk Analyst",
             "Compliance Officer","IT Executive","Collections Agent","Accounts Officer","HR Executive"]
ALERT_TYPES=["Suspicious Transaction","High Value Transaction","Unusual Location"]
COMPLAINT_DESC=[
    "Unauthorized transaction on my card","Reward points not credited after purchase",
    "Wrong bill amount generated","Card blocked without any reason",
    "Failed transaction amount not refunded","Double charge for same transaction",
    "Unable to make online payment","Suspicious transaction not done by me",
    "Card declined at merchant POS","CVV mismatch error during online payment",
    "Cashback not received as promised","EMI conversion not processed",
    "Statement not received on email","Credit limit not updated after payment",
    "Offer discount not applied at checkout","Reward points expiring without notice",
    "Duplicate payment deducted","Card not working abroad","PIN change not working",
    "Mobile banking app showing wrong balance"]
OFFER_NAMES=[
    "Amazon Shopping Festival","Weekend Dining Delight","MakeMyTrip Holiday Deal",
    "Fuel Surcharge Waiver","Movie Ticket Cashback","Grocery Discount",
    "Flight Booking Offer","Electronics Cashback","Fashion Sale Offer","Travel Miles Bonus",
    "Restaurant Weekend Offer","Petrol Pump Cashback","OTT Subscription Discount",
    "Health & Wellness Offer","Book Fair Discount","Gaming Store Offer",
    "Home Appliance Deal","Gold Purchase Bonus","International Spend Reward","New Year Offer",
    "Diwali Shopping Bonus","Holi Special Cashback","Independence Day Sale","Republic Day Offer",
    "Valentine Dining Offer","Summer Travel Deal","Monsoon Shopping Bonus","Winter Wardrobe Offer"]

# ----------------------------------------------------------------------
#  MAIN – create DB, tables and fill them
# ----------------------------------------------------------------------
def build_database():
    # ------------------------------------------------------------------
    #  Remove old DB (if any) and open a new connection
    # ------------------------------------------------------------------
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    cur  = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")      # enforce FK constraints

    # ------------------------------------------------------------------
    #  1️⃣  CREATE ALL TABLES (identical to the schema you posted)
    # ------------------------------------------------------------------
    cur.executescript("""
    CREATE TABLE USERS(
        user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        username  TEXT UNIQUE NOT NULL,
        password  TEXT NOT NULL,
        role      TEXT NOT NULL CHECK(role IN ('admin','employee','cardholder')),
        linked_id INTEGER );
    
    CREATE TABLE CARD_HOLDER(
        Holder_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        F_name         TEXT NOT NULL,
        L_name         TEXT NOT NULL,
        DOB            TEXT NOT NULL,
        Gender         TEXT NOT NULL,
        Phone_no       TEXT NOT NULL UNIQUE,
        Email          TEXT NOT NULL UNIQUE,
        Address        TEXT,
        Annual_income  REAL,
        Credit_score   INTEGER CHECK(Credit_score BETWEEN 300 AND 900) );
    
    CREATE TABLE CREDIT_CARD(
        Card_no           TEXT PRIMARY KEY,
        Card_type         TEXT NOT NULL,
        Card_status       TEXT NOT NULL CHECK(Card_status IN ('Active','Blocked','Expired')),
        Credit_limit      REAL NOT NULL,
        Available_balance REAL NOT NULL,
        Issue_date        TEXT NOT NULL,
        Expiry_date       TEXT NOT NULL,
        CVV               TEXT NOT NULL,
        Holder_id         INTEGER NOT NULL REFERENCES CARD_HOLDER(Holder_id) );
    
    CREATE TABLE BANK_ACCOUNT(
        Account_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        Account_no   TEXT NOT NULL UNIQUE,
        Bank_name    TEXT NOT NULL,
        Account_type TEXT NOT NULL CHECK(Account_type IN ('Savings','Current')),
        IFSC_code   TEXT NOT NULL,
        Holder_id    INTEGER NOT NULL REFERENCES CARD_HOLDER(Holder_id) );
    
    CREATE TABLE TRANSACTIONS(
        Txn_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        Txn_date     TEXT NOT NULL,
        Txn_time     TEXT NOT NULL,
        Txn_amount   REAL NOT NULL,
        Txn_type     TEXT NOT NULL,
        Merchant_name TEXT NOT NULL,
        Txn_status   TEXT NOT NULL CHECK(Txn_status IN ('Success','Failed','Pending')),
        Card_no      TEXT NOT NULL REFERENCES CREDIT_CARD(Card_no) );
    
    CREATE TABLE BILL_STATEMENT(
        Bill_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        Bill_date        TEXT NOT NULL,
        Due_date         TEXT NOT NULL,
        Total_due        REAL NOT NULL,
        Min_due          REAL NOT NULL,
        Bill_status      TEXT NOT NULL CHECK(Bill_status IN ('Paid','Unpaid','Overdue')),
        Statement_period TEXT NOT NULL,
        Card_no          TEXT NOT NULL REFERENCES CREDIT_CARD(Card_no) );
    
    CREATE TABLE PAYMENT(
        Payment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        Payment_date   TEXT NOT NULL,
        Payment_amt    REAL NOT NULL,
        Payment_mode   TEXT NOT NULL CHECK(Payment_mode IN ('UPI','NEFT','IMPS','Debit Card')),
        Payment_status TEXT NOT NULL CHECK(Payment_status IN ('Success','Pending','Failed')),
        Bill_id        INTEGER NOT NULL REFERENCES BILL_STATEMENT(Bill_id),
        Account_id     INTEGER NOT NULL REFERENCES BANK_ACCOUNT(Account_id) );
    
    CREATE TABLE REWARD_POINTS(
        Reward_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        Points_earned   INTEGER NOT NULL DEFAULT 0,
        Points_redeemed INTEGER NOT NULL DEFAULT 0,
        Points_balance  INTEGER NOT NULL DEFAULT 0,
        Expiry_date     TEXT NOT NULL,
        Card_no         TEXT NOT NULL UNIQUE REFERENCES CREDIT_CARD(Card_no) );
    
    CREATE TABLE CARD_EMPLOYEE(
        Emp_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        F_name      TEXT NOT NULL,
        L_name      TEXT NOT NULL,
        Department  TEXT NOT NULL,
        Role        TEXT NOT NULL,
        Contact_no  TEXT NOT NULL UNIQUE );
    
    CREATE TABLE FRAUD_ALERT(
        Alert_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        Alert_date    TEXT NOT NULL,
        Alert_type    TEXT NOT NULL CHECK(Alert_type IN ('Suspicious Transaction','High Value Transaction','Unusual Location')),
        Alert_status  TEXT NOT NULL CHECK(Alert_status IN ('Open','Resolved')),
        Description   TEXT,
        Txn_id        INTEGER NOT NULL REFERENCES TRANSACTIONS(Txn_id),
        Card_no       TEXT NOT NULL REFERENCES CREDIT_CARD(Card_no) );
    
    CREATE TABLE COMPLAINT(
        Complaint_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        Complaint_date TEXT NOT NULL,
        Description    TEXT NOT NULL,
        Status         TEXT NOT NULL CHECK(Status IN ('Open','In Progress','Resolved')),
        Resolution     TEXT,
        Holder_id      INTEGER NOT NULL REFERENCES CARD_HOLDER(Holder_id),
        Emp_id         INTEGER NOT NULL REFERENCES CARD_EMPLOYEE(Emp_id),
        Txn_id         INTEGER REFERENCES TRANSACTIONS(Txn_id) );
    
    CREATE TABLE OFFERS(
        Offer_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        Offer_name      TEXT NOT NULL,
        Discount_pct    REAL NOT NULL CHECK(Discount_pct BETWEEN 1 AND 100),
        Min_txn_amt     REAL NOT NULL,
        Valid_from      TEXT NOT NULL,
        Valid_to        TEXT NOT NULL,
        Card_type       TEXT NOT NULL,
        Offer_status    TEXT NOT NULL CHECK(Offer_status IN ('Active','Expired','Inactive')) );
    
    CREATE TABLE CARD_OFFER(
        Card_no      TEXT NOT NULL REFERENCES CREDIT_CARD(Card_no),
        Offer_id     INTEGER NOT NULL REFERENCES OFFERS(Offer_id),
        Applied_date TEXT NOT NULL,
        Points_bonus INTEGER DEFAULT 0,
        PRIMARY KEY(Card_no,Offer_id) );
    """)

    # ------------------------------------------------------------------
    #  Helper lists that keep track of the IDs we just inserted.
    #  They are needed because many tables reference others.
    # ------------------------------------------------------------------
    holder_ids = []   # contains the autoincrement ids of CARD_HOLDER (1‑100)
    card_nos   = []   # list of the 100 generated card numbers
    account_ids= []   # autoinc ids of BANK_ACCOUNT
    txn_ids    = []   # autoinc ids of TRANSACTIONS
    bill_ids   = []   # autoinc ids of BILL_STATEMENT

    # ------------------------------------------------------------------
    #  2️⃣ CARD_HOLDER  (100 rows)
    # ------------------------------------------------------------------
    print("⏳ Inserting CARD_HOLDER …")
    used_phones = set()
    used_emails = set()
    for i in range(100):
        gender = "Male" if i < 60 else "Female"
        fname  = random.choice(FNAMES_M if gender == "Male" else FNAMES_F)
        lname  = random.choice(LNAMES)
        dob    = rdate("1970-01-01", "2000-12-31")
        phone  = f"9{random.randint(100000000, 999999999)}"
        while phone in used_phones:
            phone = f"9{random.randint(100000000, 999999999)}"
        used_phones.add(phone)

        email  = f"{fname.lower()}.{lname.lower()}{i+1}@{'gmail' if i%3==0 else 'yahoo' if i%3==1 else 'outlook'}.com"
        while email in used_emails:
            email = f"{fname.lower()}{i+1}x@gmail.com"
        used_emails.add(email)

        city   = random.choice(CITIES)
        area   = random.choice(AREAS)
        address= f"{random.choice('ABCDEFGH')}-{random.randint(1,999)}, {area}, {city}"
        income = random.randint(2, 50) * 25000          # 50 k – 1.25 M
        score  = random.randint(500, 890)             # realistic credit‑score range

        cur.execute("""INSERT INTO CARD_HOLDER
                       (F_name,L_name,DOB,Gender,Phone_no,Email,Address,Annual_income,Credit_score)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (fname,lname,dob,gender,phone,email,address,income,score))
        holder_ids.append(cur.lastrowid)

    # ------------------------------------------------------------------
    #  3️⃣ CREDIT_CARD  (100 rows – one per holder)
    # ------------------------------------------------------------------
    print("⏳ Inserting CREDIT_CARD …")
    for i, holder_id in enumerate(holder_ids, start=1):
        # generate a unique 16‑digit (but SQLite TEXT) card number
        while True:
            prefix = random.choice(['4111','5222','3711','4532','5425','4916','5234'])
            number = prefix + ''.join(str(random.randint(0,9)) for _ in range(12))
            if number not in card_nos:
                break
        card_nos.append(number)

        card_type = random.choice(CARD_TYPES)
        # decide credit limit according to the holder's score (simple rule)
        score = cur.execute("SELECT Credit_score FROM CARD_HOLDER WHERE Holder_id = ?", (holder_id,)).fetchone()[0]
        if   score >= 750: limit = random.choice([150000,200000,250000])
        elif score >= 650: limit = random.choice([50000,80000,100000])
        else:               limit = random.choice([20000,30000,40000])

        avail   = round(limit * random.uniform(0.1, 1.0), -2)   # round to nearest 100
        status  = random.choices(['Active','Blocked','Expired'], weights=[80,12,8])[0]
        issue   = rdate("2020-01-01","2025-12-31")
        expiry  = str(date.fromisoformat(issue) + timedelta(days=365*3))
        cvv     = f"{random.randint(100,999)}"

        cur.execute("""INSERT INTO CREDIT_CARD
                       (Card_no,Card_type,Card_status,Credit_limit,Available_balance,
                        Issue_date,Expiry_date,CVV,Holder_id)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (number, card_type, status, limit, avail, issue, expiry, cvv, holder_id))

    # ------------------------------------------------------------------
    #  4️⃣ BANK_ACCOUNT  (100 rows – one per holder)
    # ------------------------------------------------------------------
    print("⏳ Inserting BANK_ACCOUNT …")
    for i, holder_id in enumerate(holder_ids, start=1):
        while True:
            acc_no = str(random.randint(1000000000000, 9999999999999))
            if acc_no not in [row[0] for row in cur.execute("SELECT Account_no FROM BANK_ACCOUNT")]:
                break
        bidx   = random.randint(0, len(BANKS)-1)
        bank   = BANKS[bidx]
        ifsc   = f"{IFSC_PFX[bidx]}0{random.randint(100000,999999)}"
        acctyp = random.choice(["Savings","Savings","Current"])   # more Savings than Current
        cur.execute("""INSERT INTO BANK_ACCOUNT
                       (Account_no,Bank_name,Account_type,IFSC_code,Holder_id)
                       VALUES (?,?,?,?,?)""",
                    (acc_no, bank, acctyp, ifsc, holder_id))
        account_ids.append(cur.lastrowid)

    # ------------------------------------------------------------------
    #  5️⃣ TRANSACTIONS  (100 rows – mainly on Active cards)
    # ------------------------------------------------------------------
    print("⏳ Inserting TRANSACTIONS …")
    active_cards = [cn for cn, st in zip(card_nos,
                       [cur.execute("SELECT Card_status FROM CREDIT_CARD WHERE Card_no = ?", (cn,)).fetchone()[0] for cn in card_nos])
                     if st == "Active"]
    if len(active_cards) < 20:          # fallback – just use the first 50 cards
        active_cards = card_nos[:50]

    for _ in range(100):
        card   = random.choice(active_cards)
        tdate  = rdate("2025-06-01","2026-03-10")
        ttime  = rtime()
        amount = random.choice([random.randint(100,500),
                               random.randint(500,2000),
                               random.randint(2000,10000),
                               random.randint(10000,50000)])
        ttype  = random.choice(TXN_TYPES)
        merchant = random.choice(MERCHANTS)
        status = random.choices(['Success','Failed','Pending'], weights=[80,12,8])[0]
        cur.execute("""INSERT INTO TRANSACTIONS
                       (Txn_date,Txn_time,Txn_amount,Txn_type,Merchant_name,Txn_status,Card_no)
                       VALUES (?,?,?,?,?,?,?)""",
                    (tdate, ttime, amount, ttype, merchant, status, card))
        txn_ids.append(cur.lastrowid)

    # ------------------------------------------------------------------
    #  6️⃣ BILL_STATEMENT  (100 rows – one per random card)
    # ------------------------------------------------------------------
    print("⏳ Inserting BILL_STATEMENT …")
    periods = ["January 2025","February 2025","March 2025","April 2025","May 2025",
               "June 2025","July 2025","August 2025","September 2025","October 2025",
               "November 2025","December 2025","January 2026","February 2026","March 2026"]
    for _ in range(100):
        card   = random.choice(card_nos)
        period = random.choice(periods)
        bdate  = rdate("2025-01-01","2026-03-01")
        ddate  = str(date.fromisoformat(bdate) + timedelta(days=20))
        total  = round(random.randint(1000,80000), -2)      # round to nearest 100
        mindue = round(total * 0.1, 2)
        status = random.choices(['Paid','Unpaid','Overdue'], weights=[50,30,20])[0]
        cur.execute("""INSERT INTO BILL_STATEMENT
                       (Bill_date,Due_date,Total_due,Min_due,Bill_status,Statement_period,Card_no)
                       VALUES (?,?,?,?,?,?,?)""",
                    (bdate, ddate, total, mindue, status, period, card))
        bill_ids.append(cur.lastrowid)

    # ------------------------------------------------------------------
    #  7️⃣ PAYMENT  (100 rows – one per random bill + random account)
    # ------------------------------------------------------------------
    print("⏳ Inserting PAYMENT …")
    pay_modes = ['UPI','NEFT','IMPS','Debit Card']
    for _ in range(100):
        bill_id    = random.choice(bill_ids)
        account_id = random.choice(account_ids)
        pdate      = rdate("2025-01-01","2026-03-10")
        # retrieve the bill amount so the payment looks realistic
        total_due = cur.execute("SELECT Total_due FROM BILL_STATEMENT WHERE Bill_id = ?", (bill_id,)).fetchone()[0]
        pamt      = round(total_due * random.uniform(0.5, 1.0), -2)   # pay at least half the bill
        mode      = random.choice(pay_modes)
        status    = random.choices(['Success','Pending','Failed'], weights=[70,20,10])[0]
        cur.execute("""INSERT INTO PAYMENT
                       (Payment_date,Payment_amt,Payment_mode,Payment_status,Bill_id,Account_id)
                       VALUES (?,?,?,?,?,?)""",
                    (pdate, pamt, mode, status, bill_id, account_id))

    # ------------------------------------------------------------------
    #  8️⃣ REWARD_POINTS  (100 rows – one per card)
    # ------------------------------------------------------------------
    print("⏳ Inserting REWARD_POINTS …")
    for cn in card_nos:
        earned   = random.randint(500, 50000)
        redeemed = random.randint(0, int(earned*0.6))
        balance  = earned - redeemed
        expiry   = rdate("2026-06-01","2028-12-31")
        cur.execute("""INSERT INTO REWARD_POINTS
                       (Points_earned,Points_redeemed,Points_balance,Expiry_date,Card_no)
                       VALUES (?,?,?,?,?)""",
                    (earned, redeemed, balance, expiry, cn))

    # ------------------------------------------------------------------
    #  9️⃣ CARD_EMPLOYEE  (100 rows)
    # ------------------------------------------------------------------
    print("⏳ Inserting CARD_EMPLOYEE …")
    used_emp_phones = set()
    for _ in range(100):
        gender = "Male" if random.random() < 0.6 else "Female"
        fname  = random.choice(FNAMES_M if gender == "Male" else FNAMES_F)
        lname  = random.choice(LNAMES)
        dept   = random.choice(DEPARTMENTS)
        role   = random.choice(EMP_ROLES)
        phone  = f"9{random.randint(800000000, 899999999)}"
        while phone in used_emp_phones:
            phone = f"9{random.randint(800000000, 899999999)}"
        used_emp_phones.add(phone)
        cur.execute("""INSERT INTO CARD_EMPLOYEE
                       (F_name,L_name,Department,Role,Contact_no)
                       VALUES (?,?,?,?,?)""",
                    (fname, lname, dept, role, phone))

    # ------------------------------------------------------------------
    # 10️⃣ FRAUD_ALERT  (100 rows – each linked to an existing transaction)
    # ------------------------------------------------------------------
    print("⏳ Inserting FRAUD_ALERT …")
    fraud_descs = [
        "Large POS at unusual hour. Multiple failed logins detected.",
        "Single purchase exceeds 80% of credit limit.",
        "International transaction from unrecognised location.",
        "Transaction attempt from unregistered device.",
        "Multiple transactions in a short time‑span.",
        "Card used in two different cities within 1 hour.",
        "High‑value ATM withdrawal at midnight.",
        "Online transaction with unusual merchant.",
        "Transaction pattern deviates from cardholder history.",
        "Repeated failed OTP attempts before transaction."
    ]
    used_txn_fraud = set()
    for _ in range(100):
        # make sure we do not reuse the same txn_id for fraud alerts
        while True:
            txn_id = random.choice(txn_ids)
            if txn_id not in used_txn_fraud:
                used_txn_fraud.add(txn_id)
                break
        alert_date = rdate("2025-06-01","2026-03-10")
        a_type     = random.choice(ALERT_TYPES)
        a_status   = random.choices(['Open','Resolved'], weights=[40,60])[0]
        a_desc     = random.choice(fraud_descs)
        # card_no can be fetched from the transaction we just selected
        card_no = cur.execute("SELECT Card_no FROM TRANSACTIONS WHERE Txn_id = ?", (txn_id,)).fetchone()[0]
        cur.execute("""INSERT INTO FRAUD_ALERT
                       (Alert_date,Alert_type,Alert_status,Description,Txn_id,Card_no)
                       VALUES (?,?,?,?,?,?)""",
                    (alert_date, a_type, a_status, a_desc, txn_id, card_no))

    # ------------------------------------------------------------------
    # 11️⃣ COMPLAINT  (100 rows – random holder, employee (and maybe a txn)
    # ------------------------------------------------------------------
    print("⏳ Inserting COMPLAINT …")
    resolution_texts = [
        "Issue resolved. Amount refunded within 5‑7 working days.",
        "Card unblocked after identity verification.",
        "Bill corrected and updated statement sent.",
        "Duplicate charge reversed successfully.",
        "Reward points credited manually.",
        "Offer discount applied as cashback.",
        "Under investigation by fraud team.",
        "Customer informed. No action required.",
        "Escalated to senior team for review.",
        None, None, None    # some complaints stay without a resolution yet
    ]
    for _ in range(100):
        holder_id = random.randint(1, len(holder_ids))
        emp_id    = random.randint(1, 100)                # we have exactly 100 employees
        txn_id    = random.choice(txn_ids) if random.random() > 0.3 else None
        cdate     = rdate("2025-01-01","2026-03-10")
        descr     = random.choice(COMPLAINT_DESC)
        status    = random.choices(['Open','In Progress','Resolved'], weights=[30,30,40])[0]
        resolution= random.choice(resolution_texts) if status == 'Resolved' else None
        cur.execute("""INSERT INTO COMPLAINT
                       (Complaint_date,Description,Status,Resolution,Holder_id,Emp_id,Txn_id)
                       VALUES (?,?,?,?,?,?,?)""",
                    (cdate, descr, status, resolution, holder_id, emp_id, txn_id))

    # ------------------------------------------------------------------
    # 12️⃣ OFFERS  (100 rows – a mixture of active/expired/inactive)
    # ------------------------------------------------------------------
    print("⏳ Inserting OFFERS …")
    for i in range(100):
        name   = random.choice(OFFER_NAMES) + f" {2025 + i//50}"
        disc   = random.choice([5,8,10,12,15,18,20,25,30])
        mintxn = random.choice([500,1000,1500,2000,3000,5000,8000,10000])
        vfrom  = rdate("2024-01-01","2026-01-01")
        vto    = str(date.fromisoformat(vfrom) + timedelta(days=random.randint(30,180)))
        ctype  = random.choice(CARD_TYPES + ["All Cards"])
        status = random.choices(['Active','Expired','Inactive'], weights=[50,35,15])[0]
        cur.execute("""INSERT INTO OFFERS
                       (Offer_name,Discount_pct,Min_txn_amt,Valid_from,Valid_to,Card_type,Offer_status)
                       VALUES (?,?,?,?,?,?,?)""",
                    (name, disc, mintxn, vfrom, vto, ctype, status))

    # ------------------------------------------------------------------
    # 13️⃣ CARD_OFFER  (100 rows – random many‑to‑many between cards & offers)
    # ------------------------------------------------------------------
    print("⏳ Inserting CARD_OFFER …")
    offer_ids = [row[0] for row in cur.execute("SELECT Offer_id FROM OFFERS")]
    card_offer_set = set()
    while len(card_offer_set) < 100:
        card_no = random.choice(card_nos)
        oid     = random.choice(offer_ids)
        if (card_no, oid) in card_offer_set:
            continue
        card_offer_set.add((card_no, oid))
        adate   = rdate("2024-06-01","2026-03-01")
        bonus   = random.choice([0,50,100,150,200,250,300,500])
        cur.execute("""INSERT INTO CARD_OFFER
                       (Card_no,Offer_id,Applied_date,Points_bonus)
                       VALUES (?,?,?,?)""",
                    (card_no, oid, adate, bonus))

    # ------------------------------------------------------------------
    # 14️⃣ USERS  (admin + employees + card‑holders)
    # ------------------------------------------------------------------
    print("⏳ Inserting USERS …")
    #  admin
    cur.execute("INSERT INTO USERS(username,password,role,linked_id) VALUES('admin','admin123','admin',NULL)")
    #  employees (use the same order as CARD_EMPLOYEE)
    for i in range(1, 101):
        cur.execute("INSERT INTO USERS(username,password,role,linked_id) VALUES(?,?,'employee',?)",
                    (f"emp{i}", "emp123", i))
    #  card‑holders (use the same order as CARD_HOLDER)
    for i in range(1, 101):
        cur.execute("INSERT INTO USERS(username,password,role,linked_id) VALUES(?,?,'cardholder',?)",
                    (f"user{i}", "card123", i))

    # ------------------------------------------------------------------
    #  FINALISE
    # ------------------------------------------------------------------
    conn.commit()
    conn.close()
    print("\n✅  Database created →", DB_NAME)
    print("\n🗒️  Sample login credentials")
    print("   Admin      → admin / admin123")
    print("   Employee   → emp1  / emp123")
    print("   Cardholder → user1 / card123")
    print("\n   (You can also log‑in with any `user{n}` / `emp{n}` generated above)")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    build_database()
