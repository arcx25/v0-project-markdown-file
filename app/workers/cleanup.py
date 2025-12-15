"""Cleanup worker for expired data."""

from celery import shared_task
from sqlalchemy import select, and_, delete
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.user import AuthChallenge, Session
from app.models.payment import Deposit, DepositStatus


@celery_app.task(name="app.workers.cleanup.cleanup_expired_data")
def cleanup_expired_data():
    """Clean up expired data."""
    import asyncio
    asyncio.run(_cleanup_expired_data())


async def _cleanup_expired_data():
    """Async implementation of cleanup."""
    
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        
        # Clean up expired auth challenges
        stmt = delete(AuthChallenge).where(
            and_(
                AuthChallenge.expires_at < now,
                AuthChallenge.used == True
            )
        )
        result = await db.execute(stmt)
        print(f"[v0] Cleaned up {result.rowcount} expired auth challenges")
        
        # Clean up expired sessions
        stmt = delete(Session).where(
            and_(
                Session.expires_at < now,
                Session.is_active == False
            )
        )
        result = await db.execute(stmt)
        print(f"[v0] Cleaned up {result.rowcount} expired sessions")
        
        # Mark expired deposits as expired
        stmt = select(Deposit).where(
            and_(
                Deposit.status == DepositStatus.PENDING,
                Deposit.expires_at < now
            )
        )
        result = await db.execute(stmt)
        expired_deposits = result.scalars().all()
        
        for deposit in expired_deposits:
            deposit.status = DepositStatus.EXPIRED
        
        print(f"[v0] Marked {len(expired_deposits)} deposits as expired")
        
        await db.commit()
