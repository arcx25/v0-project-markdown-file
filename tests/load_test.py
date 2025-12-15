"""Load testing with Locust."""

from locust import HttpUser, task, between
import json


class VaultUser(HttpUser):
    """Simulated ARCHITECT // VAULT user."""
    
    wait_time = between(1, 5)
    
    def on_start(self):
        """Setup: Register and login."""
        # Register
        self.client.post("/api/auth/register", json={
            "username": f"loadtest_{self.userId}",
            "role": "buyer",
            "pgp_public_key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\ntest\n-----END PGP PUBLIC KEY BLOCK-----"
        })
        
        # Login (simplified for load testing)
        self.token = "test_token"
    
    @task(3)
    def browse_leads(self):
        """Browse available leads."""
        self.client.get("/api/leads/")
    
    @task(2)
    def view_lead(self):
        """View specific lead."""
        self.client.get("/api/leads/1")
    
    @task(1)
    def create_lead(self):
        """Create a new lead."""
        self.client.post("/api/leads/", json={
            "title": "Load Test Lead",
            "category": "technology",
            "scope": "local",
            "summary": "This is a test lead created during load testing. " * 10,
            "evidence_types": ["documents"]
        }, headers={"Authorization": f"Bearer {self.token}"})
    
    @task(2)
    def browse_listings(self):
        """Browse support listings."""
        self.client.get("/api/listings/")
    
    @task(1)
    def health_check(self):
        """Check system health."""
        self.client.get("/health")


class VendorUser(HttpUser):
    """Simulated vendor user."""
    
    wait_time = between(2, 8)
    
    def on_start(self):
        """Setup: Register as vendor."""
        self.client.post("/api/auth/register", json={
            "username": f"vendor_{self.userId}",
            "role": "vendor",
            "pgp_public_key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\ntest\n-----END PGP PUBLIC KEY BLOCK-----"
        })
        self.token = "test_token"
    
    @task(5)
    def browse_leads(self):
        """Browse leads as vendor."""
        self.client.get("/api/leads/")
    
    @task(2)
    def express_interest(self):
        """Express interest in a lead."""
        self.client.post("/api/leads/1/interest", json={
            "pitch": "I am interested in this lead because... " * 20
        }, headers={"Authorization": f"Bearer {self.token}"})
