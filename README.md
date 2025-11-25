# RawLink Backend

This is the backend API for the RawLink platform, responsible for handling users, listings, orders, wallet transactions, and authentication. Built with **Django REST Framework** and designed for secure, scalable, and maintainable APIs.

---

## **Table of Contents**

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Setup Instructions](#setup-instructions)
4. [Environment Variables](#environment-variables)
5. [Database](#database)
6. [API Endpoints](#api-endpoints)
7. [Running Tests](#running-tests)
8. [Deployment](#deployment)

---

## **Features**

- User authentication (registration, login, roles: buyer/vendor)
- Listings management (CRUD for recyclables)
- Order management and status updates
- Wallet management (credits, transactions)
- Real-time transaction and chat handling (optional)
- Sustainability impact tracking

---

## **Tech Stack**

- Python 3.11+
- Django 4.x
- Django REST Framework
- PostgreSQL (or SQLite for development)
- Channels / WebSockets (for chat, optional)
- Redis (optional, for caching & channels)

---

## **Setup Instructions**

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/rawlink-backend.git
cd rawlink-backend


python -m venv venv
source venv/bin/activate  # Linux / Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

The API will be available at http://127.0.0.1:8000/ 

** currently it is hosted on Render: https://rawlink-api.onrender.com/admin/