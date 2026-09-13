# Event-Driven Inventory & Order Management System

A backend-focused **enterprise inventory and order management system** built with **FastAPI and PostgreSQL**, featuring JWT authentication, role-based access control, concurrency-safe inventory management, event-driven processing, event logging, and user notifications.

The system is designed to demonstrate real-world backend engineering concepts such as **transaction management, concurrency control, asynchronous event processing, idempotency, and secure API design**.

---

## 🚀 Features

### 🔐 Authentication & Authorization

- JWT-based authentication
- Secure user registration and login
- Role-Based Access Control (RBAC)
- Protected API endpoints
- Role-based access to inventory and order operations

### 📦 Product Management

- Create products
- View products
- Update product information
- Delete products
- Maintain inventory/stock quantities
- Stock validation during order processing

### 🛒 Order Management

- Create orders
- View orders
- Cancel orders
- Validate requested quantities against available stock
- Automatically update inventory when orders are created
- Restore inventory when orders are cancelled

### ⚡ Concurrency-Safe Inventory

The system handles simultaneous orders for the same product using **database row-level locking**.

This prevents race conditions such as:

```text
Available Stock = 5

Request A → buys 5
Request B → buys 5

Without locking:
Both requests may see stock = 5 ❌

With row locking:
Request A → locks row → updates stock → commits
Request B → waits → sees updated stock → rejected ✅
```

PostgreSQL's `SELECT ... FOR UPDATE` mechanism is used to ensure that stock cannot be incorrectly oversold.

### 📡 Event-Driven Architecture

The application uses an event-driven workflow to decouple business operations from downstream processing.

Examples of events include:

- `ORDER_CREATED`
- `ORDER_CANCELLED`
- `LOW_STOCK`

A lightweight in-process message queue is used to publish and process events.

```text
Order API
    │
    ▼
Create/Cancel Order
    │
    ▼
Publish Event
    │
    ▼
Message Queue
    │
    ▼
Event Consumer
    │
    ├── Update event log
    ├── Detect low stock
    └── Create user notification
```

### 🧾 Event Logging

Events are persisted in PostgreSQL for traceability and auditing.

Each event contains information such as:

- Event ID
- Event type
- Associated entity
- Event payload
- Processing status
- Timestamp

This provides a persistent record of system activity.

### 🔁 Event Idempotency

The event-processing layer prevents the same event from being processed multiple times.

This is important in event-driven systems because duplicate delivery or retries can otherwise result in operations being performed more than once.

### ⚠️ Low-Stock Detection

When an order reduces inventory below the configured threshold, the system generates a `LOW_STOCK` event.

```text
Order Created
      │
      ▼
Stock Updated
      │
      ▼
Stock < Threshold?
      │
     YES
      │
      ▼
LOW_STOCK Event
```

### 🔔 User Notifications

Users receive notifications for important order events, including:

- Order created
- Order cancelled
- Low-stock alerts where applicable

Notifications are generated through event processing rather than being tightly coupled to the order API.

---

## 🏗️ Architecture

The project follows a layered backend architecture with event-driven processing.

```text
                    ┌──────────────────┐
                    │     Frontend     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     FastAPI      │
                    │    REST APIs     │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
          Auth/RBAC       Products        Orders
              │              │              │
              └──────────────┼──────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │   Transactions   │
                    │  Row-Level Locks │
                    └──────────────────┘
                             │
                             │ Events
                             ▼
                    ┌──────────────────┐
                    │  Message Queue   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Event Consumer   │
                    └────────┬─────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
          Event Logs    Low Stock     Notifications
```

---

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| **Python** | Backend programming language |
| **FastAPI** | REST API framework |
| **PostgreSQL** | Relational database |
| **SQLAlchemy** | Database ORM |
| **JWT** | Authentication |
| **Pydantic** | Request/response validation |
| **Pytest** | Automated testing |
| **Docker** | Containerization/readiness |
| **In-Process Queue** | Event/message processing |
| **HTML/CSS/JavaScript** | Frontend |

---

## 🧪 Testing

The project includes automated tests covering the major backend components.

Tests include areas such as:

- Authentication
- Authorization/RBAC
- Product operations
- Order operations
- Validation
- Error handling
- Inventory management
- Concurrent order processing
- Event publishing
- Event consumption
- Event idempotency
- Low-stock events
- User notifications

Run the complete test suite with:

```bash
pytest -q
```

The concurrency tests specifically verify that simultaneous orders cannot oversell inventory.

---

## 🔒 Concurrency Control

Inventory updates are performed inside database transactions using PostgreSQL row-level locking.

The simplified workflow is:

```text
BEGIN TRANSACTION

        ↓

Lock Product Row
SELECT ... FOR UPDATE

        ↓

Check Available Stock

        ↓

Update Stock

        ↓

Create Order

        ↓

Publish Event

        ↓

COMMIT
```

This ensures that two concurrent transactions cannot modify the same inventory record incorrectly.

---

## 🔄 Event Processing

A typical order workflow looks like this:

### Order Creation

```text
POST /orders
      │
      ▼
Validate Request
      │
      ▼
Lock Inventory
      │
      ▼
Check Stock
      │
      ▼
Create Order
      │
      ▼
Update Stock
      │
      ▼
Publish ORDER_CREATED
      │
      ▼
Process Event
      │
      ├── Store Event Log
      ├── Check Low Stock
      └── Create Notification
```

### Order Cancellation

```text
Cancel Order
     │
     ▼
Restore Stock
     │
     ▼
Publish ORDER_CANCELLED
     │
     ▼
Process Event
     │
     ├── Store Event Log
     └── Create Notification
```

---

## 🗄️ Database

PostgreSQL is used as the primary persistent data store.

The database maintains information related to:

- Users
- Products
- Orders
- Order items
- Events
- Notifications

Database migrations are used to manage schema changes.

---

## 📁 Project Structure

The project is organized into separate modules for maintainability and separation of concerns.

```text
project/
│
├── app/
│   ├── routes/
│   │   ├── auth
│   │   ├── products
│   │   ├── orders
│   │   └── ...
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── events/
│   ├── notifications/
│   └── ...
│
├── tests/
│
├── migrations/
│
├── frontend/
│
├── requirements.txt
├── Dockerfile
└── README.md
```

> The exact file structure may vary depending on the current implementation.

---

## ⚙️ Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file containing the required database and authentication configuration.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/inventory_db
SECRET_KEY=your-secret-key
```

Do **not** commit `.env` or production secrets to GitHub.

### 5. Run database migrations

Run the project's configured migration command.

### 6. Start the application

```bash
uvicorn app.main:app --reload
```

The API will then be available through the configured local server.

FastAPI's interactive API documentation can be accessed through:

```text
/docs
```

---

## 🐳 Docker

The project is Docker-ready and can be containerized for consistent development and deployment environments.

Build the image:

```bash
docker build -t inventory-order-system .
```

Run the container:

```bash
docker run -p 8000:8000 inventory-order-system
```

Database configuration should be supplied through environment variables.

---

## 📊 Core Engineering Concepts Demonstrated

This project goes beyond basic CRUD by implementing several backend engineering concepts:

- REST API development
- JWT authentication
- Role-Based Access Control
- Relational database design
- Database transactions
- Row-level locking
- Race-condition prevention
- Event-driven architecture
- Message queues
- Event consumers
- Event persistence
- Event idempotency
- Low-stock detection
- Notification processing
- Input validation
- Centralized error handling
- Automated testing
- Docker-based deployment readiness

---

## 🎯 Project Goals

The primary goal of this project is to demonstrate how a traditional inventory/order application can be designed using **enterprise backend engineering principles**.

Instead of tightly coupling every operation:

```text
Order → Stock → Notification → Logging
```

the system introduces events:

```text
Order
  │
  ▼
Event
  │
  ▼
Message Queue
  │
  ├── Logging
  ├── Notifications
  └── Inventory-related processing
```

This provides better separation of concerns and creates a foundation that can be extended with additional consumers and services.

---

## 🔮 Future Improvements

Potential future extensions include:

- Redis caching
- Dedicated background workers
- Email notifications
- Pagination and filtering
- Advanced search
- Distributed message broker such as Kafka or RabbitMQ
- Observability and centralized logging
- Cloud deployment
- Microservice decomposition

These are intentionally outside the current scope of the project.

---

## 👨‍💻 Author

**Abhiram Raghunand**

Built as an academic enterprise application and extended into a portfolio/resume-oriented backend project.

---

## 📄 License

This project is intended for educational and portfolio purposes.