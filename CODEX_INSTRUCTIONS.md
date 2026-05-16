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
