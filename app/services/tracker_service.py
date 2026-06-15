import time
import requests
import validators
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from ..models import Target, PingLog, TargetStatus, User
from sqlalchemy.orm import joinedload
from .email_service import send_welcome_email, send_tracking_update_email, send_daily_report_email, send_alert_email
from ..extensions import scheduler, db
from ..utils.decorators import with_app_context

@with_app_context
def run_global_ping_cycle(app):
    BATCH_SIZE = 50
    page = 1
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        while True:
            target_batch = Target.query.filter_by(status=TargetStatus.ACTIVE).paginate(page=page, per_page=BATCH_SIZE, error_out=False).items
            
            if not target_batch:
                break
            
            for target in target_batch:
                executor.submit(_execute_individual_ping, app, target.id)

            page += 1

@with_app_context   
def run_quarantine_cycle(app):
    BATCH_SIZE = 50
    page = 1
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        while True:
            target_batch = Target.query.filter_by(status=TargetStatus.QUARANTINED).paginate(page=page, per_page=BATCH_SIZE, error_out=False).items
            
            if not target_batch:
                break
            
            for target in target_batch:
                executor.submit(_execute_individual_ping, app, target.id)
        page += 1 

@with_app_context
def run_inactive_ping_cycle(app):
    inactive_batch = Target.query.filter_by(status=TargetStatus.INACTIVE).all()
        
    with ThreadPoolExecutor(max_workers=2) as executor: 
        for target in inactive_batch:
            executor.submit(_execute_individual_ping, app, target.id)  

@with_app_context
def _execute_individual_ping(app, target_id):
    target = Target.query.get(target_id)
    if not target:
        return
    
    try:
        start_time = time.time()
        response = requests.get(target.url, timeout=5)
        response_time = time.time() - start_time
        is_online = response.status_code < 400  
        status_code = response.status_code
    except requests.RequestException:
        response_time = None
        is_online = False
        status_code = -1

    
    ping_log = PingLog(
        target_id=target_id,
        response_time=response_time,
        is_online=is_online,
        status_code=status_code
    )
    target.last_ping = datetime.utcnow()
    db.session.add(ping_log)

    _transition_target_status(target, is_online)
    db.session.commit()
    
def _transition_target_status(target, is_online: bool):
    if is_online:
        target.consecutive_failures = 0
        if target.status == TargetStatus.QUARANTINED:
            target.status = TargetStatus.ACTIVE
            target.status_changed_at = datetime.utcnow()
        
        elif target.status == TargetStatus.INACTIVE:
            target.status = TargetStatus.ACTIVE
            target.status_changed_at = datetime.utcnow()
            _run_recovery_alert(target, datetime.utcnow())
    else:
        target.consecutive_failures += 1
        if target.status == TargetStatus.ACTIVE:
            if target.consecutive_failures > 30:
                target.status = TargetStatus.QUARANTINED
                target.consecutive_failures = 0
                target.status_changed_at = datetime.utcnow()
        
        elif target.status == TargetStatus.QUARANTINED:
            if target.consecutive_failures > 12:
                target.status = TargetStatus.INACTIVE
                target.status_changed_at = datetime.utcnow()
                _run_downtime_alert(target, datetime.utcnow())

def _run_downtime_alert(target, timestamp):
    """Safely extracts users and queues a non-blocking downtime notification."""
    if target.users:
        for user in target.users:
            if user.email:
                send_alert_email(user.email, target.url, timestamp, is_recovery=False)

def _run_recovery_alert(target, timestamp):
    """Safely extracts users and queues a non-blocking recovery notification."""
    if target.users:
        for user in target.users:
            if user.email:
                send_alert_email(user.email, target.url, timestamp, is_recovery=True)

@with_app_context                  
def run_daily_reporting_cycle(app):
    BATCH_SIZE = 100
    page = 1
    last_24h = datetime.utcnow() - timedelta(days=1)
    while True:
        user_batch = User.query.options(
        joinedload(User.targets).joinedload(Target.ping_logs)).filter( PingLog.timestamp >= last_24h ).paginate(page=page, per_page=BATCH_SIZE, error_out=False).items
            
        if not user_batch:
            break
            
        for user in user_batch:
               compile_and_send_daily_report(user, last_24h)

        page += 1


def compile_and_send_daily_report(user, last_24h):
    if not user or not user.targets:
        return
    report_data = []
    for target in user.targets:
        ping_logs = [log for log in target.ping_logs if log.timestamp >= last_24h]
        if ping_logs:
            total_pings = len(ping_logs)
            online_pings = sum(1 for log in ping_logs if log.is_online)
            uptime_percentage = (online_pings / total_pings) * 100 if total_pings > 0 else 0
            avg_response_time = sum(log.response_time for log in ping_logs if log.response_time is not None) / online_pings if online_pings > 0 else None

            report_data.append({
                'target_url': target.url,
                'uptime_percentage': uptime_percentage,
                'avg_response_time': avg_response_time,
                'status': 'Online' if ping_logs[-1].is_online else 'Offline'
            })
    if report_data:
        send_daily_report_email(user.email, report_data)

def add_new_target(url:str)->tuple[dict, int]:
    if Target.query.filter_by(url=url).first():
        return {'error': 'Target already exists'}, 400

    new_target = Target(url=url)
    db.session.add(new_target)
    db.session.commit()
    return {'message': 'Target added successfully'}, 201

def process_user_tracking(email: str, targets_input) -> tuple[dict, int]:
    user = User.query.filter_by(email=email).first()
    new_user = False
    if not user:
        user = User(email=email)
        db.session.add(user)
        db.session.commit()
        new_user = True
    if isinstance(targets_input, str):
        target_urls = [targets_input]
    elif isinstance(targets_input, list):
        target_urls = targets_input
    else:
        return {'error': 'Invalid targets format'}, 400
    
    invalid_urls = []
    valid_urls = []
    already_tracked_urls = []

    for url in target_urls:
        if not validators.url(url):
            invalid_urls.append(url)
            continue  
        target = Target.query.filter_by(url=url).first()
        if not target:
            target = Target(url=url)
            db.session.add(target)
            db.flush()  
        if target in user.targets:
            already_tracked_urls.append(url)
        else:
            user.targets.append(target)
            valid_urls.append(url)  
        
    db.session.commit()
    all_current_urls = [t.url for t in user.targets]
    info = {
        'message': 'Tracking updated',
        'invalid_urls': invalid_urls if invalid_urls else None,
        'valid_urls': valid_urls if valid_urls else None,
        'already_tracked_urls': already_tracked_urls if already_tracked_urls else None,
        'current_tracked_urls': all_current_urls if all_current_urls and new_user else None
    }
    if new_user:
        send_welcome_email(user.email, info)
    else:
        send_tracking_update_email(user.email, info)
        
    return info, 200

def get_ping_logs_for_target(url: str) -> tuple[dict, int]:
    target = Target.query.filter_by(url=url).first()
    if not target:
        return {'error': 'Target not found, please add target'}, 404
    
    ping_log = PingLog.query.filter_by(target_id=target.id).order_by(PingLog.timestamp.desc()).first()
    if not ping_log:
        return {'error': 'No ping logs found for this target'}, 404
    
    return ping_log.to_dict(), 200

def get_user_targets(email: str) -> tuple[dict, int]:
    user = User.query.filter_by(email=email).first()
    if not user:
        return {'error': 'User not found'}, 404
    
    targets = [target.to_dict() for target in user.targets]
    return {'targets': targets}, 200

