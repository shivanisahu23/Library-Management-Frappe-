
# Library Management System - Frappe/ERPNext App

A custom Frappe app built for Klaimify Pvt. Ltd. as part of the ERPNext Developer Assessment.

## Overview
Digitizes and automates all core library operations with full ERPNext accounting integration.

## Features
- Book catalog with category, rack location, and copy tracking
- Member management with Student, Staff, and Public member types
- Book issue and return with automatic due date calculation
- Automatic fine calculation for overdue returns (₹5/day)
- ERPNext accounting integration — Sales Invoice on fine, Payment Entry on payment
- Daily scheduler for overdue detection and email notifications
- 4 Script Reports: Overdue Books, Fine Collection, Member Activity, Book Utilization
- Dashboard with 5 number cards
- Role-based access control: Library Administrator, Library Staff, Accounts Staff, Management

## Tech Stack
- Frappe Framework (Python + JavaScript)
- ERPNext (for Customer, Sales Invoice, Payment Entry)
- MariaDB

## Installation
```bash
bench get-app https://github.com/shivanisahu23/Library-Management-Frappe-
bench --site yoursite.com install-app library_management
bench --site yoursite.com migrate
```

## DocTypes
| DocType | Type | Purpose |
|---|---|---|
| Book | Master | Book catalog with copy tracking |
| Book Category | Master | Category classification |
| Member Type | Master | Student / Staff / Public with privileges |
| Library Member | Master | Member registration, links to ERPNext Customer |
| Library Settings | Single | Global config — loan period, fine rate, email |
| Book Issue | Transaction | Book lending record |
| Book Return | Transaction | Return with auto fine creation |
| Library Fine | Transaction | Auto-created fine, links to Sales Invoice |
| Fine Payment | Transaction | Payment record, links to Payment Entry |

## Reports
- **Overdue Books** — All overdue issues with days overdue and fine accrued
- **Fine Collection** — Fines raised vs collected, filterable by date and member type
- **Member Activity** — Issue/return/fine summary per member
- **Book Utilization** — Most/least issued books with utilization percentage

## Roles & Permissions
- **Library Administrator** — Full access to all DocTypes
- **Library Staff** — Issue/return books, record payments, view members
- **Accounts Staff** — Read-only on fines and payments
- **Management** — Dashboard and reports only

## Developer
Shivani Sahu
