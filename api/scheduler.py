from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
import logging

from .tasks import auto_reactivate_users

logger = logging.getLogger(__name__)

def delete_old_job_executions(max_age=604_800):
    """Delete old job executions (default: 7 days)."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.add_jobstore(DjangoJobStore(), "default")

def start():
    # Run auto-reactivation every 1 minute
    scheduler.add_job(
        auto_reactivate_users,
        "interval",
        minutes=1,
        id="auto_reactivate_users",
        replace_existing=True,
    )

    # Clean old jobs weekly (Monday at midnight)
    scheduler.add_job(
        delete_old_job_executions,
        "cron",
        day_of_week="mon",
        hour=0,
        minute=0,
        id="delete_old_jobs",
        replace_existing=True,
    )

    try:
        scheduler.start()
    except Exception as e:
        logger.error(f"❌ APScheduler failed to start: {e}")
