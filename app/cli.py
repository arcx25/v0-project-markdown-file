"""CLI management tool for ARCHITECT // VAULT."""

import asyncio
import sys
from typing import Optional

import click
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.pgp_service import PGPService


@click.group()
def cli():
    """ARCHITECT // VAULT management CLI."""
    pass


@cli.command()
@click.option('--username', prompt=True, help='Admin username')
@click.option('--pgp-key-file', prompt=True, type=click.Path(exists=True), help='Path to PGP public key file')
async def create_admin(username: str, pgp_key_file: str):
    """Create a new admin user."""
    async with AsyncSessionLocal() as db:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.username == username)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            click.echo(f"Error: User '{username}' already exists")
            sys.exit(1)
        
        # Read PGP key
        with open(pgp_key_file, 'r') as f:
            pgp_public_key = f.read()
        
        # Create admin user
        admin = User(
            username=username,
            role="admin",
            pgp_public_key=pgp_public_key,
            is_active=True,
            is_admin=True
        )
        
        db.add(admin)
        await db.commit()
        
        click.echo(f"Admin user '{username}' created successfully")


@cli.command()
@click.option('--username', prompt=True, help='Username to verify')
async def verify_vendor(username: str):
    """Verify a vendor account."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            click.echo(f"Error: User '{username}' not found")
            sys.exit(1)
        
        if user.role != "vendor":
            click.echo(f"Error: User '{username}' is not a vendor")
            sys.exit(1)
        
        user.is_verified = True
        await db.commit()
        
        click.echo(f"Vendor '{username}' verified successfully")


@cli.command()
async def stats():
    """Display platform statistics."""
    async with AsyncSessionLocal() as db:
        # Count users by role
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        vendor_count = sum(1 for u in users if u.role == "vendor")
        buyer_count = sum(1 for u in users if u.role == "buyer")
        admin_count = sum(1 for u in users if u.role == "admin")
        
        click.echo("=== ARCHITECT // VAULT Statistics ===")
        click.echo(f"Total Users: {len(users)}")
        click.echo(f"Vendors: {vendor_count}")
        click.echo(f"Buyers: {buyer_count}")
        click.echo(f"Admins: {admin_count}")


@cli.command()
@click.option('--output', default='platform_keys.txt', help='Output file for keys')
async def generate_platform_keys(output: str):
    """Generate platform PGP keys."""
    pgp = PGPService()
    
    click.echo("Generating platform PGP keys...")
    
    # Generate keys (this is a placeholder - actual implementation would use GPG)
    click.echo(f"Keys would be generated and saved to {output}")
    click.echo("In production, use the scripts/generate_platform_keys.py script")


def main():
    """Main CLI entry point."""
    cli(_anyio_backend="asyncio")


if __name__ == "__main__":
    main()
