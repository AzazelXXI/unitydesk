class NotificationSystem {
  constructor() {
    this.notificationList = document.getElementById("notificationList");
    this.notificationBadge = document.getElementById("notificationBadge");
    this.pollInterval = 30000; // Poll every 30 seconds as fallback
    this.websocket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second delay
    this.init();
  }

  async init() {
    await this.loadNotifications();
    this.initWebSocket();
    this.startPolling(); // Keep polling as fallback
  }

  initWebSocket() {
    try {
      // Get current user ID from the template context or a data attribute
      const userId = this.getCurrentUserId();
      if (!userId) {
        console.warn("No user ID found, falling back to polling only");
        return;
      }

      // Create WebSocket connection
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws/notifications/${userId}`;

      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log("WebSocket connected for real-time notifications");
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleWebSocketMessage(data);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      this.websocket.onclose = () => {
        console.log("WebSocket disconnected");
        this.scheduleReconnect();
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    } catch (error) {
      console.error("Error initializing WebSocket:", error);
    }
  }
  getCurrentUserId() {
    // Try multiple methods to get user ID
    const userElement = document.body;
    if (userElement && userElement.getAttribute("data-user-id")) {
      const userId = userElement.getAttribute("data-user-id");
      if (userId && userId !== "") {
        console.log("Found user ID from body:", userId);
        return userId;
      }
    }
    if (typeof window.currentUserId !== "undefined" && window.currentUserId) {
      console.log("Found user ID from global variable:", window.currentUserId);
      return window.currentUserId;
    }
    const anyUserElement = document.querySelector("[data-user-id]");
    if (anyUserElement) {
      const userId = anyUserElement.getAttribute("data-user-id");
      if (userId && userId !== "") {
        console.log("Found user ID from any element:", userId);
        return userId;
      }
    }
    console.warn("No user ID found using any method");
    return null;
  }
  handleWebSocketMessage(data) {
    console.log("Received WebSocket message:", data);
    switch (data.type) {
      case "task_status_update":
        this.showRealTimeNotification(data.data);
        this.loadNotifications(); // Refresh notification list
        break;
      case "task_assignment":
        this.showRealTimeNotification(data.data);
        this.loadNotifications(); // Refresh notification list
        break;
      case "connection_established":
        console.log("WebSocket connection established:", data.data.message);
        break;
      case "heartbeat_response":
        // Handle heartbeat response if needed
        break;
      default:
        console.log("Unknown WebSocket message type:", data.type);
    }
  }
  showRealTimeNotification(data) {
    // Show a browser toast notification
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(data.message, {
        icon: "/static/icon.png", // Add your app icon
        tag: `task-${data.task_id}`, // Prevent duplicate notifications
      });
    }
    // Show an in-app toast
    this.showToast(data.message, "info");
  }
  showToast(message, type = "info") {
    // Create a Bootstrap toast
    const toastContainer = this.getOrCreateToastContainer();
    const toastId = "toast-" + Date.now();
    const toastHtml = `
      <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">
            ${this.escapeHtml(message)}
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>
    `;
    toastContainer.insertAdjacentHTML("beforeend", toastHtml);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    // Remove toast element after it's hidden
    toastElement.addEventListener("hidden.bs.toast", () => {
      toastElement.remove();
    });
  }
  getOrCreateToastContainer() {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container position-fixed top-0 end-0 p-3";
      container.style.zIndex = "1055";
      document.body.appendChild(container);
    }
    return container;
  }
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max WebSocket reconnection attempts reached");
      return;
    }
    this.reconnectAttempts++;
    console.log(
      `Scheduling WebSocket reconnection attempt ${this.reconnectAttempts} in ${this.reconnectDelay}ms`
    );
    setTimeout(() => {
      this.initWebSocket();
    }, this.reconnectDelay);
    // Exponential backoff
    this.reconnectDelay *= 2;
  }
  async loadNotifications() {
    try {
      const response = await fetch("/api/notifications/", {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin", // Include cookies for authentication
      });
      if (response.ok) {
        const notifications = await response.json();
        this.renderNotifications(notifications);
        this.updateBadge(notifications.filter((n) => !n.is_read).length);
      } else if (response.status === 401) {
        console.warn("User not authenticated, notifications disabled");
        // Don't show error for unauthenticated users
        this.notificationList.innerHTML =
          '<li><span class="dropdown-item-text text-muted">Please log in to see notifications</span></li>';
      } else {
        console.error("Failed to load notifications:", response.status);
      }
    } catch (error) {
      console.error("Error loading notifications:", error);
    }
  }
  renderNotifications(notifications) {
    if (notifications.length === 0) {
      this.notificationList.innerHTML =
        '<li><span class="dropdown-item-text text-muted">No new notifications</span></li>';
      return;
    }
    const notificationHtml = notifications
      .map((notification) => {
        const timeAgo = this.formatTimeAgo(new Date(notification.created_at));
        const unreadClass = notification.is_read ? "" : "unread";
        return `
        <li>
          <div class="notification-item ${unreadClass}" onclick="markAsRead(${
          notification.id
        })">
            <div class="notification-title">${this.escapeHtml(
              notification.title
            )}</div>
            <div class="notification-message">${this.escapeHtml(
              notification.message
            )}</div>
            <div class="notification-time">${timeAgo}</div>
          </div>
        </li>
      `;
      })
      .join("");
    this.notificationList.innerHTML = notificationHtml;
  }
  updateBadge(count) {
    if (count > 0) {
      this.notificationBadge.textContent = count > 99 ? "99+" : count;
      this.notificationBadge.style.display = "block";
    } else {
      this.notificationBadge.style.display = "none";
    }
  }
  async markAsRead(notificationId) {
    try {
      const response = await fetch(
        `/api/notifications/${notificationId}/mark-read`,
        {
          method: "PUT",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
          credentials: "same-origin",
        }
      );
      if (response.ok) {
        await this.loadNotifications(); // Refresh notifications
      } else if (response.status === 401) {
        console.warn("User not authenticated");
      }
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  }
  async markAllAsRead() {
    try {
      // Get unread notifications
      const response = await fetch("/api/notifications/?unread_only=true");
      if (response.ok) {
        const unreadNotifications = await response.json();
        // Mark each as read
        const promises = unreadNotifications.map((notification) =>
          fetch(`/api/notifications/${notification.id}/mark-read`, {
            method: "PUT",
            headers: { Accept: "application/json" },
          })
        );
        await Promise.all(promises);
        await this.loadNotifications(); // Refresh notifications
      }
    } catch (error) {
      console.error("Error marking all notifications as read:", error);
    }
  }
  startPolling() {
    setInterval(() => {
      this.loadNotifications();
    }, this.pollInterval);
  }
  formatTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  }
  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
  // Request notification permission if not already granted
  async requestNotificationPermission() {
    if ("Notification" in window && Notification.permission === "default") {
      const permission = await Notification.requestPermission();
      console.log("Notification permission:", permission);
    }
  }
  // Clean up WebSocket on page unload
  destroy() {
    if (this.websocket) {
      this.websocket.close();
    }
  }
}
// Global functions
async function markAsRead(notificationId) {
  await notificationSystem.markAsRead(notificationId);
}
async function markAllAsRead() {
  await notificationSystem.markAllAsRead();
}
// Initialize when DOM is loaded
let notificationSystem;
document.addEventListener("DOMContentLoaded", function () {
  notificationSystem = new NotificationSystem();
  // Request notification permission
  notificationSystem.requestNotificationPermission();
});
// Clean up WebSocket on page unload
window.addEventListener("beforeunload", function () {
  if (notificationSystem) {
    notificationSystem.destroy();
  }
});
// Set current user ID for WebSocket connection
// The following block is meant to be rendered by Jinja2 in the HTML template, not in the JS file.
// Please set window.currentUserId in the template, not here.
// Set active navigation based on current path
document.addEventListener("DOMContentLoaded", function () {
  const currentPath = window.location.pathname;
  const sidebarLinks = document.querySelectorAll(".sidebar .nav-link");
  sidebarLinks.forEach((link) => {
    const href = link.getAttribute("href");
    if (href && currentPath.startsWith(href) && href !== "/") {
      link.classList.add("active");
    } else if (href === "/" && currentPath === "/") {
      link.classList.add("active");
    } else if (
      href === "/dashboard" &&
      (currentPath === "/" || currentPath === "/dashboard")
    ) {
      link.classList.add("active");
    }
  });
});
