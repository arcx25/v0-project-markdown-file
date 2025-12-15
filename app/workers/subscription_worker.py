"""
Celery worker for subscription management tasks.
Checks for expiring subscriptions and handles grace periods.
"""
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

from app.config import settings
from app.services.subscription_service import subscription_service

logger = logging.getLogger(__name__)

celery_app = Celery('subscription_worker')
celery_app.conf.broker_url = settings.CELERY_BROKER_URL
celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Create async engine for Celery tasks
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@celery_app.task(name='check_expiring_subscriptions')
def check_expiring_subscriptions():
    """Check for expiring subscriptions and handle grace periods."""
    import asyncio
    
    async def _check():
        async with async_session() as db:
            processed = await subscription_service.check_expiring_subscriptions(db)
            logger.info(f"Processed {processed} expiring subscriptions")
            return processed
    
    return asyncio.run(_check())


@celery_app.task(name='check_pending_subscription_payments')
def check_pending_subscription_payments():
    """Check for confirmed subscription payments."""
    import asyncio
    from sqlalchemy import select
    from app.models.payment import Deposit, DepositStatus, DepositPurpose
    from app.services.monero_service import monero_service
    
    async def _check():
        async with async_session() as db:
            # Get pending subscription deposits
            result = await db.execute(
                select(Deposit)
                .where(Deposit.purpose == DepositPurpose.SUBSCRIPTION)
                .where(Deposit.status.in_([DepositStatus.PENDING, DepositStatus.CONFIRMING]))
            )
            deposits = result.scalars().all()
            
            confirmed_count = 0
            for deposit in deposits:
                status_changed = await monero_service.check_deposit_status(db, deposit)
                
                if status_changed and deposit.status == DepositStatus.CONFIRMED:
                    # Process subscription activation
                    success = await subscription_service.process_subscription_payment(db, deposit)
                    if success:
                        confirmed_count += 1
            
            logger.info(f"Confirmed {confirmed_count} subscription payments")
            return confirmed_count
    
    return asyncio.run(_check())


# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    'check-expiring-subscriptions': {
        'task': 'check_expiring_subscriptions',
        'schedule': 3600.0,  # Every hour
    },
    'check-pending-subscription-payments': {
        'task': 'check_pending_subscription_payments',
        'schedule': 300.0,  # Every 5 minutes
    },
}
