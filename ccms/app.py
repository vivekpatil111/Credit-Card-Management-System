from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3, os, csv, io
from datetime import date
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "ccms_secret_key_2024"
DB = "ccms.db"

# ─── DB HELPER ───────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ─── AUTH DECORATORS ─────────────────────────────────────────
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─── AUTH ROUTES ─────────────────────────────────────────────
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM USERS WHERE username=? AND password=?",
                          (username, password)).fetchone()
        db.close()
        if user:
            session['user_id']   = user['user_id']
            session['username']  = user['username']
            session['role']      = user['role']
            session['linked_id'] = user['linked_id']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'employee':
                return redirect(url_for('emp_dashboard'))
            else:
                return redirect(url_for('ch_dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role     = request.form['role']
        db = get_db()
        try:
            if role == 'cardholder':
                db.execute("""
                    INSERT INTO CARD_HOLDER(F_name,L_name,DOB,Gender,Phone_no,
                                           Email,Address,Annual_income,Credit_score)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (request.form['f_name'], request.form['l_name'],
                     request.form['dob'], request.form['gender'],
                     request.form['phone'], request.form['email'],
                     request.form['address'],
                     float(request.form['income']),
                     int(request.form['credit_score'])))
                db.commit()
                linked_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

                db.execute("""
                    INSERT INTO BANK_ACCOUNT(Account_no,Bank_name,Account_type,IFSC_code,Holder_id)
                    VALUES(?,?,?,?,?)""",
                    (request.form['account_no'], request.form['bank_name'],
                     request.form['account_type'], request.form['ifsc'],
                     linked_id))
                db.commit()

                db.execute("INSERT INTO USERS(username,password,role,linked_id) VALUES(?,?,?,?)",
                           (username, password, 'cardholder', linked_id))
                db.commit()

            elif role == 'employee':
                db.execute("""
                    INSERT INTO CARD_EMPLOYEE(F_name,L_name,Department,Role,Contact_no)
                    VALUES(?,?,?,?,?)""",
                    (request.form['f_name'], request.form['l_name'],
                     request.form['department'], request.form['emp_role'],
                     request.form['phone']))
                db.commit()
                linked_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

                db.execute("INSERT INTO USERS(username,password,role,linked_id) VALUES(?,?,?,?)",
                           (username, password, 'employee', linked_id))
                db.commit()

            db.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.close()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('register.html')

# ══════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ══════════════════════════════════════════════════════════════
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    db = get_db()
    stats = {
        'total_holders':   db.execute("SELECT COUNT(*) FROM CARD_HOLDER").fetchone()[0],
        'active_cards':    db.execute("SELECT COUNT(*) FROM CREDIT_CARD WHERE Card_status='Active'").fetchone()[0],
        'blocked_cards':   db.execute("SELECT COUNT(*) FROM CREDIT_CARD WHERE Card_status='Blocked'").fetchone()[0],
        'total_txns':      db.execute("SELECT COUNT(*) FROM TRANSACTIONS").fetchone()[0],
        'failed_txns':     db.execute("SELECT COUNT(*) FROM TRANSACTIONS WHERE Txn_status='Failed'").fetchone()[0],
        'open_fraud':      db.execute("SELECT COUNT(*) FROM FRAUD_ALERT WHERE Alert_status='Open'").fetchone()[0],
        'open_complaints': db.execute("SELECT COUNT(*) FROM COMPLAINT WHERE Status='Open'").fetchone()[0],
        'active_offers':   db.execute("SELECT COUNT(*) FROM OFFERS WHERE Offer_status='Active'").fetchone()[0],
        'overdue_bills':   db.execute("SELECT COUNT(*) FROM BILL_STATEMENT WHERE Bill_status='Overdue'").fetchone()[0],
        'pending_amount':  db.execute("SELECT COALESCE(SUM(Total_due),0) FROM BILL_STATEMENT WHERE Bill_status IN ('Unpaid','Overdue')").fetchone()[0],
    }
    db.close()
    return render_template('admin/dashboard.html', stats=stats, now=date.today())

@app.route('/admin/cardholders')
@login_required
@role_required('admin')
def admin_cardholders():
    db = get_db()
    holders = db.execute("SELECT * FROM CARD_HOLDER ORDER BY Holder_id").fetchall()
    db.close()
    return render_template('admin/cardholders.html', holders=holders)

@app.route('/admin/cardholders/delete/<int:id>')
@login_required
@role_required('admin')
def admin_delete_holder(id):
    db = get_db()
    db.execute("DELETE FROM CARD_HOLDER WHERE Holder_id=?", (id,))
    db.commit()
    db.close()
    flash('Cardholder deleted.', 'success')
    return redirect(url_for('admin_cardholders'))

@app.route('/admin/cardholders/export')
@login_required
@role_required('admin')
def admin_export_holders_csv():
    db = get_db()
    rows = db.execute("SELECT * FROM CARD_HOLDER ORDER BY Holder_id").fetchall()
    db.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','First Name','Last Name','DOB','Gender',
                     'Phone','Email','Address','Annual Income','Credit Score'])
    for r in rows:
        writer.writerow(list(r))
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='cardholders.csv')

@app.route('/admin/cards')
@login_required
@role_required('admin')
def admin_cards():
    db = get_db()
    cards = db.execute("""
        SELECT CC.*, CH.F_name||' '||CH.L_name AS holder_name
        FROM CREDIT_CARD CC JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY CC.Card_status
    """).fetchall()
    db.close()
    return render_template('admin/cards.html', cards=cards, now=date.today())

@app.route('/admin/cards/toggle/<card_no>')
@login_required
@role_required('admin')
def admin_toggle_card(card_no):
    db = get_db()
    card = db.execute("SELECT Card_status FROM CREDIT_CARD WHERE Card_no=?", (card_no,)).fetchone()
    new_status = 'Blocked' if card['Card_status'] == 'Active' else 'Active'
    db.execute("UPDATE CREDIT_CARD SET Card_status=? WHERE Card_no=?", (new_status, card_no))
    db.commit()
    db.close()
    flash(f'Card {card_no} is now {new_status}.', 'success')
    return redirect(url_for('admin_cards'))

@app.route('/admin/transactions')
@login_required
@role_required('admin')
def admin_transactions():
    db = get_db()
    txns = db.execute("""
        SELECT T.*, CH.F_name||' '||CH.L_name AS holder_name, CC.Card_type
        FROM TRANSACTIONS T
        JOIN CREDIT_CARD CC ON T.Card_no=CC.Card_no
        JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY T.Txn_date DESC
    """).fetchall()
    db.close()
    return render_template('admin/transactions.html', txns=txns)

@app.route('/admin/bills')
@login_required
@role_required('admin')
def admin_bills():
    db = get_db()
    bills = db.execute("""
        SELECT B.*, CH.F_name||' '||CH.L_name AS holder_name
        FROM BILL_STATEMENT B
        JOIN CREDIT_CARD CC ON B.Card_no=CC.Card_no
        JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY B.Bill_status
    """).fetchall()
    db.close()
    return render_template('admin/bills.html', bills=bills)

@app.route('/admin/payments')
@login_required
@role_required('admin')
def admin_payments():
    db = get_db()
    payments = db.execute("""
        SELECT P.*, BA.Bank_name, BA.Account_no, BS.Statement_period,
               CH.F_name||' '||CH.L_name AS holder_name
        FROM PAYMENT P
        JOIN BILL_STATEMENT BS ON P.Bill_id=BS.Bill_id
        JOIN CREDIT_CARD CC ON BS.Card_no=CC.Card_no
        JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        JOIN BANK_ACCOUNT BA ON P.Account_id=BA.Account_id
        ORDER BY P.Payment_date DESC
    """).fetchall()
    db.close()
    return render_template('admin/payments.html', payments=payments)

@app.route('/admin/fraud')
@login_required
@role_required('admin')
def admin_fraud():
    db = get_db()
    alerts = db.execute("""
        SELECT FA.*, T.Merchant_name, T.Txn_amount,
               CH.F_name||' '||CH.L_name AS holder_name, CH.Phone_no
        FROM FRAUD_ALERT FA
        JOIN TRANSACTIONS T ON FA.Txn_id=T.Txn_id
        JOIN CREDIT_CARD CC ON FA.Card_no=CC.Card_no
        JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY FA.Alert_status, FA.Alert_date DESC
    """).fetchall()
    db.close()
    return render_template('admin/fraud.html', alerts=alerts)

@app.route('/admin/fraud/resolve/<int:id>')
@login_required
@role_required('admin')
def admin_resolve_fraud(id):
    db = get_db()
    db.execute("UPDATE FRAUD_ALERT SET Alert_status='Resolved' WHERE Alert_id=?", (id,))
    db.commit()
    db.close()
    flash('Fraud alert resolved.', 'success')
    return redirect(url_for('admin_fraud'))

@app.route('/admin/complaints')
@login_required
@role_required('admin')
def admin_complaints():
    db = get_db()
    complaints = db.execute("""
        SELECT C.*, CH.F_name||' '||CH.L_name AS holder_name,
               CE.F_name||' '||CE.L_name AS emp_name, CE.Department
        FROM COMPLAINT C
        JOIN CARD_HOLDER CH ON C.Holder_id=CH.Holder_id
        JOIN CARD_EMPLOYEE CE ON C.Emp_id=CE.Emp_id
        ORDER BY C.Status, C.Complaint_date DESC
    """).fetchall()
    db.close()
    return render_template('admin/complaints.html', complaints=complaints)

@app.route('/admin/rewards')
@login_required
@role_required('admin')
def admin_rewards():
    db = get_db()
    rewards = db.execute("""
        SELECT RP.*, CC.Card_type, CH.F_name||' '||CH.L_name AS holder_name
        FROM REWARD_POINTS RP
        JOIN CREDIT_CARD CC ON RP.Card_no=CC.Card_no
        JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY RP.Points_balance DESC
    """).fetchall()
    db.close()
    return render_template('admin/rewards.html', rewards=rewards)

@app.route('/admin/offers')
@login_required
@role_required('admin')
def admin_offers():
    db = get_db()
    offers = db.execute("SELECT * FROM OFFERS ORDER BY Offer_status, Discount_pct DESC").fetchall()
    db.close()
    return render_template('admin/offers.html', offers=offers)

@app.route('/admin/reports')
@login_required
@role_required('admin')
def admin_reports():
    db = get_db()
    top_spenders = db.execute("""
        SELECT CH.F_name||' '||CH.L_name AS name,
               COUNT(T.Txn_id) AS total_txns,
               SUM(T.Txn_amount) AS total_spent
        FROM CARD_HOLDER CH
        JOIN CREDIT_CARD CC ON CH.Holder_id=CC.Holder_id
        JOIN TRANSACTIONS T ON CC.Card_no=T.Card_no
        WHERE T.Txn_status='Success'
        GROUP BY CH.Holder_id ORDER BY total_spent DESC
    """).fetchall()
    txn_types = db.execute("""
        SELECT Txn_type, COUNT(*) AS cnt, SUM(Txn_amount) AS total
        FROM TRANSACTIONS GROUP BY Txn_type ORDER BY total DESC
    """).fetchall()
    pay_modes = db.execute("""
        SELECT Payment_mode, COUNT(*) AS cnt, SUM(Payment_amt) AS total
        FROM PAYMENT WHERE Payment_status='Success'
        GROUP BY Payment_mode ORDER BY total DESC
    """).fetchall()
    top_merchants = db.execute("""
        SELECT Merchant_name, COUNT(*) AS cnt, SUM(Txn_amount) AS total
        FROM TRANSACTIONS WHERE Txn_status='Success'
        GROUP BY Merchant_name ORDER BY total DESC LIMIT 5
    """).fetchall()

    os.makedirs('static/charts', exist_ok=True)

    fig, ax = plt.subplots(figsize=(6,3))
    ax.bar([r['Txn_type'] for r in txn_types],
           [r['total'] for r in txn_types], color='#4f8ef7')
    ax.set_title('Transaction Amount by Type')
    ax.set_ylabel('Amount (Rs)')
    plt.tight_layout()
    plt.savefig('static/charts/txn_type.png')
    plt.close()

    bill_data = db.execute(
        "SELECT Bill_status, COUNT(*) AS cnt FROM BILL_STATEMENT GROUP BY Bill_status"
    ).fetchall()
    fig, ax = plt.subplots(figsize=(4,4))
    ax.pie([r['cnt'] for r in bill_data],
           labels=[r['Bill_status'] for r in bill_data], autopct='%1.0f%%')
    ax.set_title('Bill Status Distribution')
    plt.tight_layout()
    plt.savefig('static/charts/bill_status.png')
    plt.close()

    db.close()
    return render_template('admin/reports.html',
        top_spenders=top_spenders, txn_types=txn_types,
        pay_modes=pay_modes, top_merchants=top_merchants)

@app.route('/admin/reports/export')
@login_required
@role_required('admin')
def admin_export_csv():
    db = get_db()
    rows = db.execute("""
        SELECT CH.F_name||' '||CH.L_name AS Cardholder, CC.Card_type,
               CC.Card_status, CC.Credit_limit, CC.Available_balance,
               BA.Bank_name, RP.Points_balance, BS.Bill_status, BS.Total_due
        FROM CARD_HOLDER CH
        JOIN CREDIT_CARD CC ON CH.Holder_id=CC.Holder_id
        JOIN BANK_ACCOUNT BA ON CH.Holder_id=BA.Holder_id
        JOIN REWARD_POINTS RP ON CC.Card_no=RP.Card_no
        JOIN BILL_STATEMENT BS ON CC.Card_no=BS.Card_no
    """).fetchall()
    db.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Cardholder','Card Type','Status','Credit Limit',
                     'Available Balance','Bank','Reward Points','Bill Status','Total Due'])
    for r in rows:
        writer.writerow(list(r))
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='ccms_report.csv')

# ══════════════════════════════════════════════════════════════
#  EMPLOYEE ROUTES
# ══════════════════════════════════════════════════════════════
@app.route('/employee/dashboard')
@login_required
@role_required('employee')
def emp_dashboard():
    db = get_db()
    emp = db.execute("SELECT * FROM CARD_EMPLOYEE WHERE Emp_id=?",
                     (session['linked_id'],)).fetchone()
    stats = {
        'total_cards':     db.execute("SELECT COUNT(*) FROM CREDIT_CARD").fetchone()[0],
        'active_cards':    db.execute("SELECT COUNT(*) FROM CREDIT_CARD WHERE Card_status='Active'").fetchone()[0],
        'total_txns':      db.execute("SELECT COUNT(*) FROM TRANSACTIONS").fetchone()[0],
        'open_complaints': db.execute("SELECT COUNT(*) FROM COMPLAINT WHERE Status='Open' AND Emp_id=?",
                                      (session['linked_id'],)).fetchone()[0],
        'open_fraud':      db.execute("SELECT COUNT(*) FROM FRAUD_ALERT WHERE Alert_status='Open'").fetchone()[0],
        'unpaid_bills':    db.execute("SELECT COUNT(*) FROM BILL_STATEMENT WHERE Bill_status='Unpaid'").fetchone()[0],
    }
    db.close()
    return render_template('employee/dashboard.html', emp=emp, stats=stats)

@app.route('/employee/cards')
@login_required
@role_required('employee')
def emp_cards():
    db = get_db()
    cards = db.execute("""
        SELECT CC.*, CH.F_name||' '||CH.L_name AS holder_name, CH.Phone_no
        FROM CREDIT_CARD CC JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY CC.Card_status
    """).fetchall()
    holders = db.execute(
        "SELECT Holder_id, F_name||' '||L_name AS name FROM CARD_HOLDER"
    ).fetchall()
    db.close()
    return render_template('employee/cards.html', cards=cards, holders=holders, now=date.today())

@app.route('/employee/cards/issue', methods=['POST'])
@login_required
@role_required('employee')
def emp_issue_card():
    db = get_db()
    card_no     = request.form['card_no']
    expiry_date = request.form['expiry_date']

    existing = db.execute(
        "SELECT Card_no FROM CREDIT_CARD WHERE Card_no=?", (card_no,)
    ).fetchone()

    if existing:
        db.close()
        flash(f'Error: Card number {card_no} already exists. Use a different number.', 'danger')
        return redirect(url_for('emp_cards'))

    try:
        db.execute("""
            INSERT INTO CREDIT_CARD(Card_no,Card_type,Card_status,Credit_limit,
                                    Available_balance,Issue_date,Expiry_date,CVV,Holder_id)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (card_no, request.form['card_type'], 'Active',
             float(request.form['credit_limit']), float(request.form['credit_limit']),
             request.form['issue_date'], expiry_date,
             request.form['cvv'], int(request.form['holder_id'])))
        db.commit()

        db.execute("""
            INSERT INTO REWARD_POINTS(Points_earned,Points_redeemed,Points_balance,Expiry_date,Card_no)
            VALUES(?,?,?,?,?)""",
            (0, 0, 0, expiry_date, card_no))
        db.commit()
        db.close()
        flash('Card issued successfully!', 'success')

    except Exception as e:
        db.close()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('emp_cards'))

@app.route('/employee/cards/block/<card_no>')
@login_required
@role_required('employee')
def emp_block_card(card_no):
    db = get_db()
    db.execute("UPDATE CREDIT_CARD SET Card_status='Blocked' WHERE Card_no=?", (card_no,))
    db.commit()
    db.close()
    flash(f'Card {card_no} blocked.', 'warning')
    return redirect(url_for('emp_cards'))

# Employee sirf transactions monitor karta hai
@app.route('/employee/transactions')
@login_required
@role_required('employee')
def emp_transactions():
    db = get_db()
    txns = db.execute("""
        SELECT T.*, CH.F_name||' '||CH.L_name AS holder_name, CC.Card_type
        FROM TRANSACTIONS T
        JOIN CREDIT_CARD CC ON T.Card_no=CC.Card_no
        JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY T.Txn_date DESC
    """).fetchall()
    db.close()
    return render_template('employee/transactions.html', txns=txns)

@app.route('/employee/bills')
@login_required
@role_required('employee')
def emp_bills():
    db = get_db()
    bills = db.execute("""
        SELECT B.*, CH.F_name||' '||CH.L_name AS holder_name, CH.Email
        FROM BILL_STATEMENT B
        JOIN CREDIT_CARD CC ON B.Card_no=CC.Card_no
        JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY B.Bill_status
    """).fetchall()
    cards = db.execute(
        "SELECT Card_no FROM CREDIT_CARD WHERE Card_status='Active'"
    ).fetchall()
    db.close()
    return render_template('employee/bills.html', bills=bills, cards=cards)

@app.route('/employee/bills/generate', methods=['POST'])
@login_required
@role_required('employee')
def emp_generate_bill():
    db = get_db()
    total = float(request.form['total_due'])
    db.execute("""
        INSERT INTO BILL_STATEMENT(Bill_date,Due_date,Total_due,Min_due,
                                   Bill_status,Statement_period,Card_no)
        VALUES(?,?,?,?,?,?,?)""",
        (request.form['bill_date'], request.form['due_date'],
         total, round(total * 0.1, 2), 'Unpaid',
         request.form['statement_period'], request.form['card_no']))
    db.commit()
    db.close()
    flash('Bill generated!', 'success')
    return redirect(url_for('emp_bills'))

@app.route('/employee/complaints')
@login_required
@role_required('employee')
def emp_complaints():
    db = get_db()
    complaints = db.execute("""
        SELECT C.*, CH.F_name||' '||CH.L_name AS holder_name,
               CE.F_name||' '||CE.L_name AS emp_name
        FROM COMPLAINT C
        JOIN CARD_HOLDER CH ON C.Holder_id=CH.Holder_id
        JOIN CARD_EMPLOYEE CE ON C.Emp_id=CE.Emp_id
        WHERE C.Emp_id=?
        ORDER BY C.Status, C.Complaint_date DESC
    """, (session['linked_id'],)).fetchall()
    db.close()
    return render_template('employee/complaints.html', complaints=complaints)

@app.route('/employee/complaints/resolve/<int:id>', methods=['POST'])
@login_required
@role_required('employee')
def emp_resolve_complaint(id):
    db = get_db()
    db.execute("UPDATE COMPLAINT SET Status='Resolved', Resolution=? WHERE Complaint_id=?",
               (request.form['resolution'], id))
    db.commit()
    db.close()
    flash('Complaint resolved!', 'success')
    return redirect(url_for('emp_complaints'))

@app.route('/employee/fraud')
@login_required
@role_required('employee')
def emp_fraud():
    db = get_db()
    alerts = db.execute("""
        SELECT FA.*, T.Merchant_name, T.Txn_amount,
               CH.F_name||' '||CH.L_name AS holder_name
        FROM FRAUD_ALERT FA
        JOIN TRANSACTIONS T ON FA.Txn_id=T.Txn_id
        JOIN CREDIT_CARD CC ON FA.Card_no=CC.Card_no
        JOIN CARD_HOLDER CH ON CC.Holder_id=CH.Holder_id
        ORDER BY FA.Alert_status, FA.Alert_date DESC
    """).fetchall()
    db.close()
    return render_template('employee/fraud.html', alerts=alerts)

@app.route('/employee/fraud/resolve/<int:id>')
@login_required
@role_required('employee')
def emp_resolve_fraud(id):
    db = get_db()
    db.execute("UPDATE FRAUD_ALERT SET Alert_status='Resolved' WHERE Alert_id=?", (id,))
    db.commit()
    db.close()
    flash('Alert resolved.', 'success')
    return redirect(url_for('emp_fraud'))

# ══════════════════════════════════════════════════════════════
#  CARDHOLDER ROUTES
# ══════════════════════════════════════════════════════════════
@app.route('/cardholder/dashboard')
@login_required
@role_required('cardholder')
def ch_dashboard():
    hid = session['linked_id']
    db = get_db()
    holder = db.execute("SELECT * FROM CARD_HOLDER WHERE Holder_id=?", (hid,)).fetchone()
    cards  = db.execute("SELECT * FROM CREDIT_CARD WHERE Holder_id=?", (hid,)).fetchall()
    recent = db.execute("""
        SELECT T.* FROM TRANSACTIONS T
        JOIN CREDIT_CARD CC ON T.Card_no=CC.Card_no
        WHERE CC.Holder_id=? ORDER BY T.Txn_date DESC LIMIT 5
    """, (hid,)).fetchall()
    open_complaints = db.execute(
        "SELECT COUNT(*) FROM COMPLAINT WHERE Holder_id=? AND Status='Open'",
        (hid,)).fetchone()[0]
    db.close()
    return render_template('cardholder/dashboard.html',
                           holder=holder, cards=cards,
                           recent=recent, open_complaints=open_complaints)

@app.route('/cardholder/cards')
@login_required
@role_required('cardholder')
def ch_cards():
    db = get_db()
    cards = db.execute("""
        SELECT CC.*, RP.Points_balance
        FROM CREDIT_CARD CC
        LEFT JOIN REWARD_POINTS RP ON CC.Card_no=RP.Card_no
        WHERE CC.Holder_id=?
    """, (session['linked_id'],)).fetchall()
    db.close()
    return render_template('cardholder/cards.html', cards=cards, now=date.today())

# Cardholder khud transaction log karta hai
@app.route('/cardholder/transactions', methods=['GET','POST'])
@login_required
@role_required('cardholder')
def ch_transactions():
    hid = session['linked_id']
    db = get_db()
    if request.method == 'POST':
        card_no    = request.form['card_no']
        txn_amount = float(request.form['txn_amount'])
        txn_status = request.form['txn_status']

        db.execute("""
            INSERT INTO TRANSACTIONS(Txn_date,Txn_time,Txn_amount,Txn_type,
                                     Merchant_name,Txn_status,Card_no)
            VALUES(?,?,?,?,?,?,?)""",
            (request.form['txn_date'], request.form['txn_time'],
             txn_amount, request.form['txn_type'],
             request.form['merchant_name'], txn_status, card_no))
        db.commit()

        # Successful transaction pe reward points earn karo (1 pt per Rs.100)
        if txn_status == 'Success':
            earned = int(txn_amount // 100)
            if earned > 0:
                db.execute("""
                    UPDATE REWARD_POINTS
                    SET Points_earned  = Points_earned  + ?,
                        Points_balance = Points_balance + ?
                    WHERE Card_no = ?
                """, (earned, earned, card_no))
                db.commit()

        db.close()
        flash(f'Transaction logged! +{int(txn_amount // 100)} reward points earned.', 'success')
        return redirect(url_for('ch_transactions'))

    txns = db.execute("""
        SELECT T.*, CC.Card_type FROM TRANSACTIONS T
        JOIN CREDIT_CARD CC ON T.Card_no=CC.Card_no
        WHERE CC.Holder_id=? ORDER BY T.Txn_date DESC
    """, (hid,)).fetchall()
    cards = db.execute("""
        SELECT Card_no, Card_type FROM CREDIT_CARD
        WHERE Holder_id=? AND Card_status='Active'
    """, (hid,)).fetchall()
    db.close()
    return render_template('cardholder/transactions.html', txns=txns, cards=cards)

@app.route('/cardholder/bills')
@login_required
@role_required('cardholder')
def ch_bills():
    db = get_db()
    bills = db.execute("""
        SELECT B.* FROM BILL_STATEMENT B
        JOIN CREDIT_CARD CC ON B.Card_no=CC.Card_no
        WHERE CC.Holder_id=? ORDER BY B.Bill_date DESC
    """, (session['linked_id'],)).fetchall()
    db.close()
    return render_template('cardholder/bills.html', bills=bills)

@app.route('/cardholder/payments', methods=['GET','POST'])
@login_required
@role_required('cardholder')
def ch_payments():
    hid = session['linked_id']
    db = get_db()
    if request.method == 'POST':
        bill_id     = int(request.form['bill_id'])
        payment_amt = float(request.form['payment_amt'])

        db.execute("""
            INSERT INTO PAYMENT(Payment_date,Payment_amt,Payment_mode,
                                Payment_status,Bill_id,Account_id)
            VALUES(?,?,?,?,?,?)""",
            (request.form['payment_date'], payment_amt,
             request.form['payment_mode'], 'Success',
             bill_id, int(request.form['account_id'])))

        # Full payment hone par bill Paid mark karo
        bill = db.execute(
            "SELECT Total_due FROM BILL_STATEMENT WHERE Bill_id=?", (bill_id,)
        ).fetchone()
        if bill and payment_amt >= bill['Total_due']:
            db.execute(
                "UPDATE BILL_STATEMENT SET Bill_status='Paid' WHERE Bill_id=?",
                (bill_id,))

        db.commit()
        flash('Payment successful! Bill marked as Paid.', 'success')
        return redirect(url_for('ch_payments'))

    payments = db.execute("""
        SELECT P.*, BS.Statement_period, BA.Bank_name
        FROM PAYMENT P
        JOIN BILL_STATEMENT BS ON P.Bill_id=BS.Bill_id
        JOIN CREDIT_CARD CC ON BS.Card_no=CC.Card_no
        JOIN BANK_ACCOUNT BA ON P.Account_id=BA.Account_id
        WHERE CC.Holder_id=? ORDER BY P.Payment_date DESC
    """, (hid,)).fetchall()
    bills = db.execute("""
        SELECT B.Bill_id, B.Total_due, B.Statement_period
        FROM BILL_STATEMENT B
        JOIN CREDIT_CARD CC ON B.Card_no=CC.Card_no
        WHERE CC.Holder_id=? AND B.Bill_status!='Paid'
    """, (hid,)).fetchall()
    accounts = db.execute(
        "SELECT * FROM BANK_ACCOUNT WHERE Holder_id=?", (hid,)
    ).fetchall()
    db.close()
    return render_template('cardholder/payments.html',
                           payments=payments, bills=bills, accounts=accounts)

@app.route('/cardholder/rewards')
@login_required
@role_required('cardholder')
def ch_rewards():
    db = get_db()
    rewards = db.execute("""
        SELECT RP.*, CC.Card_type FROM REWARD_POINTS RP
        JOIN CREDIT_CARD CC ON RP.Card_no=CC.Card_no
        WHERE CC.Holder_id=?
    """, (session['linked_id'],)).fetchall()
    db.close()
    return render_template('cardholder/rewards.html', rewards=rewards)

@app.route('/cardholder/rewards/redeem', methods=['POST'])
@login_required
@role_required('cardholder')
def ch_redeem_points():
    hid     = session['linked_id']
    card_no = request.form['card_no']
    try:
        redeem_pts = int(request.form['redeem_points'])
    except ValueError:
        flash('Invalid points value.', 'danger')
        return redirect(url_for('ch_rewards'))

    db = get_db()

    # Check karo card us holder ka hai
    reward = db.execute("""
        SELECT RP.* FROM REWARD_POINTS RP
        JOIN CREDIT_CARD CC ON RP.Card_no=CC.Card_no
        WHERE RP.Card_no=? AND CC.Holder_id=?
    """, (card_no, hid)).fetchone()

    if not reward:
        db.close()
        flash('Invalid card.', 'danger')
        return redirect(url_for('ch_rewards'))

    if redeem_pts < 500:
        db.close()
        flash('Minimum 500 points required to redeem.', 'warning')
        return redirect(url_for('ch_rewards'))

    if redeem_pts > reward['Points_balance']:
        db.close()
        flash(f'Insufficient points. Available balance: {reward["Points_balance"]:,} pts.', 'danger')
        return redirect(url_for('ch_rewards'))

    # Points redeem karo
    db.execute("""
        UPDATE REWARD_POINTS
        SET Points_redeemed = Points_redeemed + ?,
            Points_balance  = Points_balance  - ?
        WHERE Card_no = ?
    """, (redeem_pts, redeem_pts, card_no))
    db.commit()
    db.close()

    discount = (redeem_pts // 100) * 10
    flash(f'Successfully redeemed {redeem_pts:,} points! You earned ₹{discount:,} discount voucher.', 'success')
    return redirect(url_for('ch_rewards'))

@app.route('/cardholder/complaints', methods=['GET','POST'])
@login_required
@role_required('cardholder')
def ch_complaints():
    hid = session['linked_id']
    db = get_db()
    if request.method == 'POST':
        txn_id = request.form.get('txn_id')
        db.execute("""
            INSERT INTO COMPLAINT(Complaint_date,Description,Status,
                                  Holder_id,Emp_id,Txn_id)
            VALUES(?,?,?,?,?,?)""",
            (request.form['complaint_date'], request.form['description'],
             'Open', hid, 1,
             int(txn_id) if txn_id else None))
        db.commit()
        flash('Complaint raised!', 'success')
        return redirect(url_for('ch_complaints'))
    complaints = db.execute("""
        SELECT C.*, CE.F_name||' '||CE.L_name AS emp_name
        FROM COMPLAINT C JOIN CARD_EMPLOYEE CE ON C.Emp_id=CE.Emp_id
        WHERE C.Holder_id=? ORDER BY C.Complaint_date DESC
    """, (hid,)).fetchall()
    txns = db.execute("""
        SELECT T.Txn_id, T.Merchant_name, T.Txn_amount
        FROM TRANSACTIONS T
        JOIN CREDIT_CARD CC ON T.Card_no=CC.Card_no
        WHERE CC.Holder_id=?
    """, (hid,)).fetchall()
    db.close()
    return render_template('cardholder/complaints.html',
                           complaints=complaints, txns=txns)

if __name__ == '__main__':
    if not os.path.exists(DB):
        import init_db
        init_db.build_database()
    app.run(debug=True)
    
if __name__ == '__main__':
    if not os.path.exists(DB):
        import init_db
        init_db.build_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
