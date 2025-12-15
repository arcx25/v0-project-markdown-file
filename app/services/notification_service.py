"""Notification service for sending PGP-encrypted notifications."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.pgp_service import PGPService


class NotificationService:
    """Service for sending encrypted notifications to users."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pgp_service = PGPService()
    
    async def send_notification(
        self,
        user: User,
        subject: str,
        message: str
    ) -> bool:
        """
        Send PGP-encrypted notification to user.
        
        In production, this would:
        1. Encrypt message with user's public key
        2. Store in notification queue
        3. Deliver via secure channel (Tor hidden service)
        
        Args:
            user: Recipient user
            subject: Notification subject
            message: Notification message
            
        Returns:
            True if notification sent successfully
        """
        try:
            # Encrypt the message
            encrypted_message = self.pgp_service.encrypt_message(
                message, user.pgp_public_key
            )
            
            # In production: Store in notification queue or send immediately
            # For now, just return success
            return True
            
        except Exception as e:
            # Log error
            print(f"Failed to send notification to {user.username}: {e}")
            return False
    
    async def notify_lead_interest(
        self,
        buyer: User,
        vendor: User,
        lead_title: str
    ) -> bool:
        """Notify buyer that a vendor expressed interest in their lead."""
        message = f"""
        A vendor has expressed interest in your lead: "{lead_title}"
        
        Vendor: {vendor.username}
        
        Log in to review and accept or reject this vendor.
        """
        return await self.send_notification(
            buyer,
            "New Vendor Interest",
            message
        )
    
    async def notify_acceptance(
        self,
        vendor: User,
        buyer: User,
        lead_title: str
    ) -> bool:
        """Notify vendor they were accepted for a lead."""
        message = f"""
        Congratulations! You have been accepted for the lead: "{lead_title}"
        
        Buyer: {buyer.username}
        
        You can now start a secure conversation with the buyer.
        """
        return await self.send_notification(
            vendor,
            "Lead Acceptance",
            message
        )
    
    async def notify_payment_received(
        self,
        user: User,
        amount_xmr: float,
        listing_title: str
    ) -> bool:
        """Notify user of received payment."""
        message = f"""
        Payment received for your listing: "{listing_title}"
        
        Amount: {amount_xmr} XMR
        
        The payment has been confirmed on the blockchain.
        """
        return await self.send_notification(
            user,
            "Payment Received",
            message
        )
