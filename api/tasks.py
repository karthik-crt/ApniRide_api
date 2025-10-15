from django.utils import timezone
from django.db import transaction
from .models import User
import logging

logger = logging.getLogger(__name__)

def auto_reactivate_users():
    """Re-activate suspended users whose suspension time has expired."""
    now = timezone.now()
    with transaction.atomic():
        expired_users = User.objects.filter(
            account_status="suspended",
            suspended_until__lt=now
        )

        for user in expired_users:
            user.account_status = "active"
            user.suspended_until = None
            user.save(update_fields=["account_status", "suspended_until"])
            logger.info(f" Auto reactivated user {user.id}")
