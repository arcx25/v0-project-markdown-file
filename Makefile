# ARCHITECT // VAULT - Development & Deployment Makefile

.PHONY: help deploy deploy-quick ssh logs status rollback setup clean test

help:
	@echo "ARCHITECT // VAULT - Available Commands"
	@echo ""
	@echo "Deployment:"
	@echo "  make setup         - Setup SSH access to Avalanche server"
	@echo "  make deploy        - Full deployment to Avalanche"
	@echo "  make deploy-quick  - Quick code update (no dependencies)"
	@echo "  make rollback      - Rollback to previous deployment"
	@echo ""
	@echo "Server Management:"
	@echo "  make ssh           - SSH into Avalanche server"
	@echo "  make logs          - View application logs"
	@echo "  make status        - Check service status"
	@echo ""
	@echo "Development:"
	@echo "  make test          - Run tests locally"
	@echo "  make clean         - Clean build artifacts"

setup:
	@bash deploy/avalanche/setup_ssh.sh

deploy:
	@bash deploy/avalanche/deploy_to_avalanche.sh

deploy-quick:
	@bash deploy/avalanche/quick_deploy.sh

rollback:
	@bash deploy/avalanche/rollback.sh

ssh:
	@ssh avalanche

logs:
	@ssh avalanche "journalctl -u vault-web -f"

status:
	@ssh avalanche "systemctl status vault-web vault-worker vault-beat"

test:
	@pytest tests/ -v

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -f /tmp/architect-vault-deploy.tar.gz
	@rm -f /tmp/vault.tar.gz
