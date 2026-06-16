## ✨ Key Features

- **🚀 Real-Time Monitoring:** High-frequency ping cycles for active targets every minute.
- **🛠️ Automated Lifecycle:** Targets transition between `ACTIVE`, `QUARANTINED`, and `INACTIVE` based on failure rates.
- **📧 Async Notifications:** Multi-threaded email dispatch for downtime alerts and recovery notifications.
- **📊 Daily Health Reports:** Automated summary reports delivered directly to your inbox.
- **🧵 High Concurrency:** Optimized thread pool management for background tasks (pings, emails).
- **⏰ Integrated Scheduler:** Precision scheduling with `APScheduler` for routine checks and reports.

---

## 📋 Prerequisites

- **Python:** version 3.8 or higher.
- **SMTP Provider:** A Gmail account (with an App Password) or a similar SMTP service.

---

## ⚙️ Installation & Setup

### 1. Initialize the Environment
Navigate to the project root and create a Python virtual environment:
```bash
python -m venv .venv
```

### 2. Activate the Environment
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory and populate it with your credentials:
```env
DATABASE_URL=sqlite:///uptime_sentinel.db
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
```

---

## 🚀 Running the Application

### Initialize the Database
Before launching the server for the first time, you must initialize the database schema:
```bash
flask init-db
```

### Start the Server
```bash
flask run
```
The application will be available at `http://127.0.0.1:5000`.

---

## 🛠️ CLI Reference

| Command | Description |
| :--- | :--- |
| `flask init-db` | Creates all required database tables. |
| `flask drop-db` | Removes all tables from the database (Destructive). |
