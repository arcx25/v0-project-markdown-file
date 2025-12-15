#!/usr/bin/env python3
"""Initialize admin user."""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append('.')

from app.config import get_settings
from app.models.user import User, UserRole
from app.services.pgp_service import PGPService


async def init_admin():
    """Create initial admin user."""
    settings = get_settings()
    
    if not settings.INITIAL_ADMIN_PGP_KEY:
        print("Error: INITIAL_ADMIN_PGP_KEY not set in environment")
        return
    
    # Create engine
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Import PGP key
    pgp = PGPService()
    success, fingerprint, error = pgp.import_public_key(settings.INITIAL_ADMIN_PGP_KEY)
    
    if not success:
        print(f"Error importing admin PGP key: {error}")
        return
    
    async with async_session() as session:
        # Check if admin exists
        from sqlalchemy import select
        stmt = select(User).where(User.username == settings.INITIAL_ADMIN_USERNAME)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Admin user '{settings.INITIAL_ADMIN_USERNAME}' already exists")
            return
        
        # Create admin user
        admin = User(
            username=settings.INITIAL_ADMIN_USERNAME,
            role=UserRole.ADMIN,
            pgp_fingerprint=fingerprint,
            pgp_public_key=settings.INITIAL_ADMIN_PGP_KEY
        )
        
        session.add(admin)
        await session.commit()
        
        print(f"Admin user '{settings.INITIAL_ADMIN_USERNAME}' created successfully")
        print(f"PGP Fingerprint: {fingerprint}")


if __name__ == "__main__":
    asyncio.run(init_admin())
