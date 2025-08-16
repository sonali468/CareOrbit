// Authentication utilities and session management
class AuthManager {
  constructor() {
    this.checkSessionInterval = null
    this.startSessionMonitoring()
  }

  // Start monitoring session status
  startSessionMonitoring() {
    // Check session every 5 minutes
    this.checkSessionInterval = setInterval(
      () => {
        this.checkSessionStatus()
      },
      5 * 60 * 1000,
    )

    // Check immediately
    this.checkSessionStatus()
  }

  // Check current session status
  async checkSessionStatus() {
    try {
      const response = await fetch("/api/session/status")
      const data = await response.json()

      if (!data.authenticated) {
        this.handleSessionExpired(data.message)
      }
    } catch (error) {
      console.error("Session check failed:", error)
    }
  }

  // Handle session expiration
  handleSessionExpired(message = "Session expired") {
    if (this.checkSessionInterval) {
      clearInterval(this.checkSessionInterval)
    }

    window.showAlert(message, "warning")

    setTimeout(() => {
      window.location.href = "/"
    }, 2000)
  }

  // Logout function
  async logout() {
    try {
      const response = await fetch("/logout")
      if (response.ok) {
        window.location.href = "/"
      }
    } catch (error) {
      console.error("Logout failed:", error)
      window.location.href = "/"
    }
  }

  // Stop session monitoring
  stopSessionMonitoring() {
    if (this.checkSessionInterval) {
      clearInterval(this.checkSessionInterval)
    }
  }
}

// Initialize auth manager on protected pages
if (window.location.pathname !== "/" && !window.location.pathname.includes("/login")) {
  window.authManager = new AuthManager()
}

// Add logout functionality to logout buttons
document.addEventListener("DOMContentLoaded", () => {
  const logoutButtons = document.querySelectorAll(".logout-btn")
  logoutButtons.forEach((button) => {
    button.addEventListener("click", (e) => {
      e.preventDefault()
      if (window.authManager) {
        window.authManager.logout()
      } else {
        window.location.href = "/logout"
      }
    })
  })
})

// Declare showAlert function
window.showAlert = (message, type) => {
  alert(`${type}: ${message}`)
}
