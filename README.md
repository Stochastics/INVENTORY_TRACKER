# Inventory MVP

A minimal inventory system that can be demoed quickly as a mobile-friendly web app and later expanded into a full website or phone app.

The goal of this MVP is simple:

> A worker can open the app on a phone, log in with an Employee ID and PIN, enter or scan a SKU, receive inventory, ship inventory out, adjust counts, and see the transaction history.

This is intentionally stripped down so the first version can launch quickly.

---

## MVP Scope

This version supports:

- One inventory location
- Employee login with Employee ID + PIN
- Users/employees
- Items tracked by SKU
- Current inventory quantity
- Receive inventory
- Ship out inventory
- Manual inventory adjustment
- Transaction history
- Mobile-friendly web interface
- API-first backend

This version does not include:

- Multiple sites
- Reorder levels
- Suppliers
- Purchase orders
- Complex authentication
- User roles
- Native iPhone/Android app
- Offline mode
- Accounting/invoicing logic

Those can be added later.

---

## Product Goal

The first demo should feel like a usable app, not just a backend.

A worker should be able to use a phone and do this:

```text
1. Open the web app
2. Log in with Employee ID + PIN
3. Enter SKU
4. See the item and current quantity
5. Choose Receive, Ship Out, or Adjust
6. Enter quantity
7. Add optional notes
8. Submit
9. See updated inventory
10. View transaction history
```

---

## Recommended MVP Stack

### Backend

```text
FastAPI
SQLAlchemy
PostgreSQL
Pydantic
Uvicorn
passlib or bcrypt for PIN hashing
```

### Frontend

```text
React
Vite
Mobile-first CSS
```

### Hosting

```text
Backend: Railway or Render
Database: Railway Postgres, Supabase, or Neon
Frontend: Vercel
Repository: GitHub
```

### Local Development

```text
SQLite can be used locally for speed.
PostgreSQL should be used for the hosted demo.
```

---

## High-Level Architecture

```text
Mobile Web App / Website
        |
        v
FastAPI Backend
        |
        v
PostgreSQL Database
```

Later, a native mobile app can use the same backend:

```text
iPhone App / Android App
        |
        v
Same FastAPI Backend
        |
        v
Same PostgreSQL Database
```

The backend should be API-first so the frontend can be swapped or expanded later.

---

## Core Database Tables

The stripped-down MVP only needs four tables:

```text
users
items
inventory_balances
inventory_transactions
```

---

## Table: users

Tracks employees and supports bare-bones login.

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    employee_id TEXT UNIQUE NOT NULL,
    pin_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Fields:

```text
user_id
name
employee_id
pin_hash
is_active
created_at
```

Example:

```text
user_id: 1
name: John Smith
employee_id: EMP001
pin_hash: hashed version of PIN
is_active: 1
```

Important:

```text
Do not store raw PINs.
Store only hashed PINs.
Do not delete users during normal usage.
Set is_active = 0 if an employee should no longer log in.
```

---

## Table: items

Tracks each product/item by SKU.

```sql
CREATE TABLE items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    item_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Fields:

```text
item_id
sku
item_name
description
created_at
```

Example:

```text
sku: WRNCH-001
item_name: Box of Wrenches
description: Box of adjustable wrenches
```

---

## Table: inventory_balances

Tracks the current quantity of each item.

```sql
CREATE TABLE inventory_balances (
    item_id INTEGER PRIMARY KEY,
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (item_id) REFERENCES items(item_id)
);
```

Fields:

```text
item_id
quantity_on_hand
updated_at
```

Example:

```text
item_id: 1
quantity_on_hand: 25
```

---

## Table: inventory_transactions

Tracks every inventory movement.

```sql
CREATE TABLE inventory_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    transaction_type TEXT NOT NULL,
    quantity_change INTEGER NOT NULL,

    quantity_before INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (item_id) REFERENCES items(item_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

Fields:

```text
transaction_id
item_id
user_id
transaction_type
quantity_change
quantity_before
quantity_after
notes
created_at
```

---

## Login Design

Use the `users` table for login.

Login method:

```text
Employee ID + PIN
```

Example:

```text
Employee ID: EMP001
PIN: 1234
```

The backend checks:

```text
1. Does employee_id exist?
2. Is the user active?
3. Does the PIN match the stored pin_hash?
4. If yes, return the user info and optional token.
```

For the first demo, the backend can return user info and the frontend can store the current user in local storage.

A JWT token can be added, but do not overbuild authentication for the first demo.

---

## Transaction Types

The MVP only needs three transaction types:

```text
RECEIVE
SHIP_OUT
ADJUST
```

### RECEIVE

Adds inventory.

Example:

```text
Before: 10
Change: +5
After: 15
```

### SHIP_OUT

Removes inventory.

Example:

```text
Before: 10
Change: -3
After: 7
```

The backend should reject the transaction if it would make inventory negative.

### ADJUST

Corrects inventory manually.

Example:

```text
Before: 10
Change: -2
After: 8
```

This is useful when the physical count does not match the system count.

---

## Backend Rules

The backend should enforce these rules:

1. Inventory can only change through a transaction.
2. Every transaction must record the user, item, quantity before, quantity change, quantity after, notes, and timestamp.
3. `RECEIVE` increases quantity.
4. `SHIP_OUT` decreases quantity.
5. `SHIP_OUT` cannot make inventory negative.
6. `ADJUST` can increase or decrease quantity.
7. The current balance should update immediately after each valid transaction.
8. The transaction log should never be deleted during normal usage.
9. PINs must be hashed before storage.
10. Inactive users cannot log in or create transactions.

---

## MVP API Endpoints

### Health Check

```text
GET /health
```

Returns whether the backend is running.

---

### Auth

```text
POST /login
```

Example login payload:

```json
{
  "employee_id": "EMP001",
  "pin": "1234"
}
```

Simple response for MVP:

```json
{
  "user_id": 1,
  "name": "John Smith",
  "employee_id": "EMP001"
}
```

Optional later response with token:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "name": "John Smith",
    "employee_id": "EMP001"
  }
}
```

---

### Users

```text
POST /users
GET  /users
```

Example create user payload:

```json
{
  "name": "John Smith",
  "employee_id": "EMP001",
  "pin": "1234"
}
```

The backend should hash the PIN and store it as `pin_hash`.

---

### Items

```text
POST /items
GET  /items
GET  /items/{sku}
```

Example create item payload:

```json
{
  "sku": "WRNCH-001",
  "item_name": "Box of Wrenches",
  "description": "Box of adjustable wrenches"
}
```

---

### Inventory

```text
GET  /inventory
GET  /inventory/{sku}
POST /inventory/receive
POST /inventory/ship-out
POST /inventory/adjust
```

Example receive payload:

```json
{
  "sku": "WRNCH-001",
  "user_id": 1,
  "quantity": 10,
  "notes": "Initial shipment received"
}
```

Example ship-out payload:

```json
{
  "sku": "WRNCH-001",
  "user_id": 1,
  "quantity": 3,
  "notes": "Sent to job site"
}
```

Example adjustment payload:

```json
{
  "sku": "WRNCH-001",
  "user_id": 1,
  "quantity_change": -2,
  "notes": "Physical count correction"
}
```

---

### Transactions

```text
GET /transactions
GET /transactions?sku=WRNCH-001
GET /transactions?user_id=1
```

Transaction response example:

```json
{
  "transaction_id": 1,
  "sku": "WRNCH-001",
  "item_name": "Box of Wrenches",
  "user_name": "John Smith",
  "transaction_type": "RECEIVE",
  "quantity_change": 10,
  "quantity_before": 0,
  "quantity_after": 10,
  "notes": "Initial shipment received",
  "created_at": "2026-05-15T14:30:00"
}
```

---

## Mobile Web App Screens

The first frontend should be mobile-first.

### Screen 1: Login

```text
Inventory MVP

Employee ID
[ EMP001 ]

PIN
[ 1234 ]

[ Login ]
```

---

### Screen 2: Lookup Item

```text
Enter SKU

[ WRNCH-001 ]

[ Search ]
```

Later this can support camera barcode scanning.

---

### Screen 3: Item Action

```text
Box of Wrenches
SKU: WRNCH-001
Current Quantity: 12

[ Receive ]
[ Ship Out ]
[ Adjust ]
```

---

### Screen 4: Submit Quantity

```text
Action: Receive

Quantity
[ 5 ]

Notes
[ New shipment received ]

[ Submit ]
```

---

### Screen 5: Confirmation

```text
Inventory Updated

Box of Wrenches
Previous Quantity: 12
Change: +5
New Quantity: 17

[ Done ]
```

---

### Screen 6: Transaction History

```text
Recent Activity

John Smith | RECEIVE  | WRNCH-001 | +5 | 12 -> 17
Sarah Lee  | SHIP_OUT | WRNCH-001 | -2 | 17 -> 15
```

---

## Suggested Project Structure

```text
inventory_mvp/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── auth.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── items.py
│   │       ├── inventory.py
│   │       └── transactions.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── .env.example
│
├── CODEX_INSTRUCTIONS.md
└── README.md
```

---

## Environment Variables

### Backend `.env.example`

```env
DATABASE_URL=postgresql://user:password@host:port/database
```

For local SQLite development:

```env
DATABASE_URL=sqlite:///./inventory.db
```

### Frontend `.env.example`

```env
VITE_API_BASE_URL=https://your-backend-url.com
```

---

## Running the Backend Locally

From the `backend` folder:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend docs:

```text
http://localhost:8000/docs
```

---

## Running the Frontend Locally

From the `frontend` folder:

```bash
npm install
npm run dev
```

Frontend dev server:

```text
http://localhost:5173
```

---

## Fastest Demo Deployment

Recommended quick-launch setup:

```text
GitHub repo
Railway or Render backend
Railway/Supabase/Neon PostgreSQL database
Vercel frontend
```

Suggested flow:

```text
1. Push repo to GitHub
2. Deploy backend from /backend
3. Add DATABASE_URL to backend environment variables
4. Deploy frontend from /frontend
5. Add VITE_API_BASE_URL to frontend environment variables
6. Open frontend URL on phone
7. Demo login, receive, ship-out, adjust, and transaction history
```

---

## MVP Development Order

Build in this order:

```text
1. Database models
2. PIN hashing utilities
3. Login endpoint
4. User creation
5. Item creation
6. Inventory transaction logic
7. Seed demo users/items
8. Mobile-first React frontend
9. Hosted backend
10. Hosted database
11. Hosted frontend
12. Phone demo
```

---

## Demo Data

Seed a few employees:

```text
John Smith - EMP001 - PIN 1234
Sarah Lee - EMP002 - PIN 1234
Mike Brown - EMP003 - PIN 1234
```

Seed a few items:

```text
WRNCH-001 - Box of Wrenches
HAMMR-001 - Hammer
DRILL-001 - Cordless Drill
BOLT-001 - Box of Bolts
```

Seed starting inventory:

```text
WRNCH-001: 12
HAMMR-001: 8
DRILL-001: 4
BOLT-001: 100
```

This makes the first demo easier because the app already has realistic data.

---

## First Demo Script

Use this flow during the demo:

```text
1. Open the app on a phone.
2. Log in as John Smith with EMP001 / 1234.
3. Search SKU: WRNCH-001.
4. Show current quantity: 12.
5. Receive 5.
6. Show new quantity: 17.
7. Ship out 2.
8. Show new quantity: 15.
9. Open transaction history.
10. Show both transactions with user, item, timestamp, and before/after quantities.
```

This demonstrates the full value of the MVP.

---

## How to Use Codex on This Project

Use Codex as a repo-building assistant, not as the product manager.

The README is the source of truth. Do not let Codex invent extra features unless you explicitly ask for them.

### Recommended Codex Workflow

```text
1. Create an empty GitHub repo.
2. Add this README.md.
3. Add CODEX_INSTRUCTIONS.md.
4. Open the repo with Codex.
5. Ask Codex to build one milestone at a time.
6. Review the diff after every milestone.
7. Run the app locally.
8. Commit only working changes.
```

### Codex Guardrails

Tell Codex:

```text
Do not add multiple sites.
Do not add reorder levels.
Do not add suppliers.
Do not add roles.
Do not add complex auth.
Do not create a native mobile app yet.
Do not change the database schema without asking.
Do not store raw PINs.
Do not allow inventory to go negative.
Every inventory change must create a transaction log.
```

### Codex Prompt 1: Scaffold the Project

```text
Read README.md and CODEX_INSTRUCTIONS.md.

Build the initial project structure for the Inventory MVP.

Create:
- backend FastAPI app
- SQLAlchemy database setup
- Pydantic schemas
- SQLAlchemy models
- route modules
- frontend React + Vite app
- basic mobile-first layout
- requirements.txt
- package.json

Do not implement extra features beyond the README.
Do not add multiple sites, roles, suppliers, reorder levels, or complex auth.
Use the four-table schema from the README.
```

### Codex Prompt 2: Build Backend Models and Auth

```text
Implement the backend models and basic login system.

Requirements:
- users table with user_id, name, employee_id, pin_hash, is_active, created_at
- items table
- inventory_balances table
- inventory_transactions table
- PIN hashing utility
- POST /users should hash the provided PIN
- POST /login should verify employee_id and PIN
- inactive users cannot log in
- do not store raw PINs
- add simple tests for PIN hashing and login behavior
```

### Codex Prompt 3: Build Inventory Logic

```text
Implement the inventory transaction logic.

Requirements:
- POST /inventory/receive
- POST /inventory/ship-out
- POST /inventory/adjust
- GET /inventory
- GET /inventory/{sku}
- GET /transactions
- GET /transactions?sku=...
- GET /transactions?user_id=...

Rules:
- every inventory change creates a transaction row
- RECEIVE adds inventory
- SHIP_OUT removes inventory
- SHIP_OUT cannot make inventory negative
- ADJUST can add or remove inventory
- each transaction stores quantity_before and quantity_after
- current balance updates after each valid transaction
- do not allow inactive users to create transactions
```

### Codex Prompt 4: Seed Demo Data

```text
Add a seed script for demo data.

Create users:
- John Smith, EMP001, PIN 1234
- Sarah Lee, EMP002, PIN 1234
- Mike Brown, EMP003, PIN 1234

Create items:
- WRNCH-001, Box of Wrenches
- HAMMR-001, Hammer
- DRILL-001, Cordless Drill
- BOLT-001, Box of Bolts

Create starting inventory:
- WRNCH-001: 12
- HAMMR-001: 8
- DRILL-001: 4
- BOLT-001: 100

Make sure seed script is idempotent so it can be run more than once without duplicating data.
```

### Codex Prompt 5: Build the Mobile Web Frontend

```text
Build the mobile-first React frontend.

Screens:
1. Login screen with employee_id and PIN
2. SKU lookup screen
3. Item detail screen showing item name, SKU, and current quantity
4. Action buttons: Receive, Ship Out, Adjust
5. Quantity + notes form
6. Confirmation message after submit
7. Recent transaction history

Requirements:
- use VITE_API_BASE_URL for the backend URL
- store logged-in user in localStorage for the MVP
- keep styling simple and phone-friendly
- use large buttons
- make error messages clear
- do not add extra features
```

### Codex Prompt 6: Add Tests

```text
Add backend tests for the core MVP logic.

Test:
- create user hashes PIN
- login succeeds with correct PIN
- login fails with wrong PIN
- inactive user cannot log in
- receive inventory increases balance
- ship out decreases balance
- ship out cannot make balance negative
- adjust can increase balance
- adjust can decrease balance
- every inventory change creates a transaction row
- quantity_before and quantity_after are correct
```

### Codex Prompt 7: Deployment Prep

```text
Prepare the project for deployment.

Backend:
- add requirements.txt
- confirm uvicorn startup command
- confirm DATABASE_URL is read from environment variables
- add CORS config for frontend URL
- add /health endpoint

Frontend:
- confirm VITE_API_BASE_URL is used
- confirm npm run build works

Docs:
- update README with run and deploy instructions
- add any missing .env.example files

Do not change the schema or add features.
```

---

## CODEX_INSTRUCTIONS.md

Create a separate file named `CODEX_INSTRUCTIONS.md` with this content:

```text
# Codex Instructions for Inventory MVP

You are helping build a minimal inventory MVP.

The README.md is the source of truth.

Keep the project small and demoable.

Do not add features unless explicitly requested.

## Core Requirements

Use only these core tables:

- users
- items
- inventory_balances
- inventory_transactions

## Login

Use bare-bones login:

- employee_id
- PIN

Store only pin_hash.

Do not store raw PINs.

Inactive users cannot log in.

## Inventory Rules

Every inventory change must create a transaction log.

RECEIVE adds inventory.

SHIP_OUT removes inventory.

SHIP_OUT cannot make inventory negative.

ADJUST can add or remove inventory.

Each transaction must store:

- user_id
- item_id
- transaction_type
- quantity_change
- quantity_before
- quantity_after
- notes
- created_at

## Do Not Build Yet

Do not add:

- multiple sites
- reorder levels
- suppliers
- purchase orders
- roles
- admin permissions
- native mobile app
- offline mode
- accounting features
- complex auth

## Frontend

Build a simple mobile-first React web app.

It should support:

- login
- SKU lookup
- receive inventory
- ship out inventory
- adjust inventory
- transaction history

## Development Style

Prefer simple readable code.

Add tests for important backend logic.

Do not silently change the schema.

If a feature is ambiguous, choose the simplest version that supports the MVP demo.
```

---

## Later Features

After the MVP is approved, possible next features include:

- Real login tokens/JWT
- PIN reset
- Barcode scanning from phone camera
- Multiple inventory locations
- Native mobile app using React Native or Expo
- Item photos
- CSV import/export
- Admin dashboard
- Low-stock alerts
- Shipment records
- Supplier records
- Purchase order records
- Offline mode
- Audit export

---

## Guiding Principle

Keep the first version small, useful, and demoable.

The MVP only needs to answer:

```text
Who is using the app?
What item is this?
How many do we have?
Who changed the count?
When did they change it?
Why did they change it?
```
