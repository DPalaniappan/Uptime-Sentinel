# Uptime Sentinel

Uptime Sentinel is a robust Flask-based web application designed to monitor the availability of web targets. It features real-time pinging, automatic quarantine of failing targets, daily reporting, and asynchronous email notifications.

## Prerequisites

- Python 3.8 or higher
- Gmail account (for SMTP email notifications)

## Setup Instructions

### 1. Create a Virtual Environment
Navigate to the project root directory and create a virtual environment:
```bash
python -m venv .venv
```

### 2. Activate the Virtual Environment
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Linux / macOS:** `source .venv/bin/activate`

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root directory:
```env
DATABASE_URL=your-url
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password
