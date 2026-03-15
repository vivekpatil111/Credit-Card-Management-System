# Credit Card Management System (CCMS)

> **Student:** Vivek N Patil | **Roll No:** C274 | **B.Tech AIML F2** | **SAP ID:** 70532300022

---

## Table of Contents
- [Aim](#aim)
- [Problem Statement](#problem-statement)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Roles & Access](#roles--access)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Demo Credentials](#demo-credentials)

---

## Aim

To design and implement a centralized Database Management System for a Credit Card Management platform that efficiently manages cardholder information, credit cards, transactions, billing statements, reward points, fraud detection, payment processing, complaints, and promotional offers — all normalized up to the Third Normal Form (3NF).

---

## Problem Statement

Traditional credit card management systems relied on fragmented, manual, or siloed processes, resulting in:

- Difficulty tracking real-time transaction history and available credit balance
- Errors and delays in monthly bill generation and payment reconciliation
- No structured fraud detection or alert mechanism
- Inconsistent reward points tracking causing customer dissatisfaction
- Lack of a centralized complaint management system linked to specific transactions
- Data redundancy and inconsistency due to the absence of proper normalization

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Database | SQLite 3 (file-based, serverless) |
| Backend | Python 3.x |
| Web Framework | Flask |
| Frontend | HTML5, CSS3, JavaScript |
| Reporting | Matplotlib, CSV Export |
| Version Control | Git / GitHub |

---

## Features

### Admin
- Full system oversight — cardholders, cards, transactions, bills, payments
- Fraud alert monitoring and resolution
- Complaint management
- Reward points overview across all users
- Promotional offers management
- Analytical reports with charts and CSV export

### Employee
- Issue new credit cards to cardholders
- Generate monthly billing statements
- Resolve assigned complaints
- Monitor and resolve fraud alerts
- Reward points entry auto-created on card issuance

### Cardholder
- Log own transactions (earn reward points automatically)
- View credit cards and available balance
- View monthly bill statements
- Make payments from linked bank account (bill auto-marked Paid)
- Redeem reward points for discount vouchers
- Raise and track complaints

### Reward Points System
- **Earning:** ₹100 spent = 1 point (on every successful transaction)
- **Redeeming:** 100 points = ₹10 discount | Minimum 500 points per redemption

---

## Roles & Access

| Feature | Cardholder | Employee | Admin |
|---------|-----------|---------|-------|
| Login / Logout | Own account | Own account | Full access |
| Credit Cards | View own | Issue / Block | Full CRUD |
| Transactions | Log / View own | View all | Full CRUD |
| Bill Statements | View own | Generate | Full CRUD |
| Payments | Make payments | — | Full CRUD |
| Fraud Alerts | No access | View / Resolve | Full CRUD |
| Reward Points | View / Redeem | — | Full CRUD |
| Complaints | Raise / Track | Handle / Resolve | Full CRUD |
| Offers | View only | — | Full CRUD |
| Reports | No access | Limited | Full analytics |

---

## Database Schema

The system is built on 12 fully normalized relational tables:

| # | Table | Description |
|---|-------|-------------|
| 1 | `CARD_HOLDER` | Cardholder personal and financial info |
| 2 | `CREDIT_CARD` | Card details, limits, and status |
| 3 | `BANK_ACCOUNT` | Linked bank accounts per holder |
| 4 | `TRANSACTIONS` | All card transactions with status |
| 5 | `BILL_STATEMENT` | Monthly billing statements |
| 6 | `PAYMENT` | Payments made against bills |
| 7 | `REWARD_POINTS` | Points earned, redeemed, and balance |
| 8 | `FRAUD_ALERT` | Fraud alerts linked to transactions |
| 9 | `CARD_EMPLOYEE` | Employee details and departments |
| 10 | `COMPLAINT` | Cardholder complaints linked to transactions |
| 11 | `OFFERS` | Promotional offers by card type |
| 12 | `CARD_OFFER` | Many-to-many: cards and availed offers |

---
## E-R Diagram

![CCMS E-R Diagram](er_diagram.jpg)
## Project Structure

```
ccms/
├── app.py                  # Main Flask application
├── init_db.py              # Database initialization & sample data (100 rows/table)
├── ccms.db                 # SQLite database (auto-created on first run)
├── requirements.txt        # Python dependencies
├── static/
│   ├── style.css           # Global stylesheet
│   └── charts/             # Auto-generated chart images
└── templates/
    ├── base.html           # Base layout with navbar
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── admin/
    │   ├── dashboard.html
    │   ├── cardholders.html
    │   ├── cards.html
    │   ├── transactions.html
    │   ├── bills.html
    │   ├── payments.html
    │   ├── fraud.html
    │   ├── complaints.html
    │   ├── rewards.html
    │   ├── offers.html
    │   └── reports.html
    ├── employee/
    │   ├── dashboard.html
    │   ├── cards.html
    │   ├── transactions.html
    │   ├── bills.html
    │   ├── complaints.html
    │   └── fraud.html
    └── cardholder/
        ├── dashboard.html
        ├── cards.html
        ├── transactions.html
        ├── bills.html
        ├── payments.html
        ├── rewards.html
        └── complaints.html
```

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ccms.git
cd ccms
```

### 2. Install dependencies
```bash
pip install flask matplotlib
```

### 3. Run the application
```bash
python app.py
```

The database (`ccms.db`) is automatically created and populated with 100 sample records on first run.

### 4. Open in browser
```
http://127.0.0.1:5000
```

---

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Employee | `emp1` | `emp123` |
| Cardholder | `vasu` | `qwerty` |

> You can also use `emp2`, `emp3`... or `user2`, `user3`... with the same passwords.

---

## Key Business Rules

- Full bill payment automatically marks bill status as **Paid**
- Every successful transaction earns **1 reward point per ₹100 spent**
- Minimum **500 points** required for redemption
- **100 points = ₹10 discount** voucher
- Duplicate card numbers are rejected at issuance
- New card issuance automatically creates a reward points account

---

## License

This project was developed as a DBMS Case Study for academic purposes.  
**B.Tech AIML F2 — Vivek N Patil (C274)**
