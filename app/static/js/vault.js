/**
 * ARCHITECT // VAULT - Client-side JavaScript
 * Handles PGP operations, API interactions, and UI enhancements
 */

class VaultClient {
  constructor() {
    this.apiBase = "/api"
    this.init()
  }

  init() {
    // Initialize event listeners
    this.setupAuthForms()
    this.setupLeadForms()
    this.setupMessageForms()
  }

  // Authentication
  setupAuthForms() {
    const registerForm = document.getElementById("register-form")
    if (registerForm) {
      registerForm.addEventListener("submit", (e) => this.handleRegister(e))
    }

    const loginForm = document.getElementById("login-form")
    if (loginForm) {
      loginForm.addEventListener("submit", (e) => this.handleLogin(e))
    }
  }

  async handleRegister(e) {
    e.preventDefault()
    const formData = new FormData(e.target)

    const data = {
      username: formData.get("username"),
      role: formData.get("role"),
      pgp_public_key: formData.get("pgp_public_key"),
    }

    try {
      const response = await fetch(`${this.apiBase}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })

      const result = await response.json()

      if (response.ok) {
        // Show challenge for signing
        this.showChallenge(result.challenge)
      } else {
        this.showError(result.detail || "Registration failed")
      }
    } catch (error) {
      this.showError("Network error occurred")
    }
  }

  async handleLogin(e) {
    e.preventDefault()
    const username = document.getElementById("username").value

    try {
      // Step 1: Request challenge
      const challengeResponse = await fetch(`${this.apiBase}/auth/login/challenge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      })

      const challengeData = await challengeResponse.json()

      if (challengeResponse.ok) {
        this.showChallenge(challengeData.challenge)
      } else {
        this.showError(challengeData.detail || "Login failed")
      }
    } catch (error) {
      this.showError("Network error occurred")
    }
  }

  showChallenge(challenge) {
    const challengeDiv = document.getElementById("challenge-section")
    if (challengeDiv) {
      document.getElementById("challenge-text").value = challenge
      challengeDiv.style.display = "block"
    }
  }

  // Lead Management
  setupLeadForms() {
    const createLeadBtn = document.getElementById("create-lead-btn")
    if (createLeadBtn) {
      createLeadBtn.addEventListener("click", () => this.showLeadModal())
    }
  }

  async createLead(formData) {
    try {
      const response = await fetch(`${this.apiBase}/leads/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        window.location.reload()
      } else {
        const error = await response.json()
        this.showError(error.detail || "Failed to create lead")
      }
    } catch (error) {
      this.showError("Network error occurred")
    }
  }

  // Messaging
  setupMessageForms() {
    const sendMessageBtn = document.getElementById("send-message-btn")
    if (sendMessageBtn) {
      sendMessageBtn.addEventListener("click", () => this.sendMessage())
    }
  }

  async sendMessage() {
    const conversationId = document.getElementById("conversation-id").value
    const content = document.getElementById("message-content").value

    try {
      const response = await fetch(`${this.apiBase}/messages/${conversationId}/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: JSON.stringify({ content }),
      })

      if (response.ok) {
        document.getElementById("message-content").value = ""
        this.loadMessages(conversationId)
      }
    } catch (error) {
      this.showError("Failed to send message")
    }
  }

  // Utility methods
  getToken() {
    return localStorage.getItem("vault_token")
  }

  showError(message) {
    const errorDiv = document.createElement("div")
    errorDiv.className = "alert alert-error"
    errorDiv.textContent = message
    document.body.insertBefore(errorDiv, document.body.firstChild)

    setTimeout(() => errorDiv.remove(), 5000)
  }

  showSuccess(message) {
    const successDiv = document.createElement("div")
    successDiv.className = "alert alert-success"
    successDiv.textContent = message
    document.body.insertBefore(successDiv, document.body.firstChild)

    setTimeout(() => successDiv.remove(), 5000)
  }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  window.vaultClient = new VaultClient()
})
