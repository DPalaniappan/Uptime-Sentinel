from flask_sqlalchemy import SQLAlchemy
from flask_mailman import Mail
from flask_apscheduler import APScheduler
from dotenv import load_dotenv
import os
import sys
import click

# Load .env from the project root (relative to where you run the command)
load_dotenv()

db = SQLAlchemy()
mail = Mail()
scheduler = APScheduler()

def configure_extensions(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['SCHEDULER_API_ENABLED'] = True
    
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    
    
    db.init_app(app)
    mail.init_app(app)
    scheduler.init_app(app)

    # Start the scheduler only when running the server, not during CLI commands like init-db.
    # 1. WERKZEUG_RUN_MAIN covers 'flask run' with reloader (the child process).
    # 2. FLASK_RUN_FROM_CLI + 'run' in argv covers 'flask run' without reloader.
    # 3. No FLASK_RUN_FROM_CLI covers production WSGI servers (Gunicorn/uWSGI).
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or \
       (os.environ.get("FLASK_RUN_FROM_CLI") == "true" and "run" in sys.argv) or \
       (not os.environ.get("FLASK_RUN_FROM_CLI")):
        if not scheduler.running:
            scheduler.start()
            click.echo("⏰ Scheduler started successfully.")

    
    app.cli.add_command(drop_db_command)
    app.cli.add_command(init_db_command)
    
    from .services.tracker_service import run_global_ping_cycle, run_daily_reporting_cycle, run_quarantine_cycle, run_inactive_ping_cycle
    
    # Add jobs only if they don't already exist to avoid ConflictingIdErrors
    if not scheduler.get_job('ping_all_targets_job'):
        scheduler.add_job(
            id='ping_all_targets_job',
            func=run_global_ping_cycle,
            trigger='interval',
            args=[app],
            minutes=1
        )

    if not scheduler.get_job('quarantine_check_job'):
        scheduler.add_job(
            id='quarantine_check_job',
            func=run_quarantine_cycle,
            trigger='interval',
            args=[app],
            hours=2
        )

    if not scheduler.get_job('inactive_ping_job'):
        scheduler.add_job(
            id='inactive_ping_job',
            func=run_inactive_ping_cycle,
            trigger='interval',
            args=[app],
            hours=24
        )
    
    if not scheduler.get_job('dispatch_daily_emails_job'):
        scheduler.add_job(
            id='dispatch_daily_emails_job',
            func=run_daily_reporting_cycle,
            trigger='cron',
            args=[app],
            hour=8,
            minute=0
        )
    
@click.command("init-db")
def init_db_command():
    """Creates database tables cleanly via CLI."""
    from . import models
    print("Initializing database tables...")
    db.create_all()
    click.echo("✅ Database tables initialized successfully!")


@click.command("drop-db")
def drop_db_command():
    """Drops the database tables."""
    from . import models
    print("Dropping database tables...")
    db.drop_all()
    click.echo("🗑️ Database tables dropped successfully!")
