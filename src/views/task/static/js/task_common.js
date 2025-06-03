/**
 * Common JavaScript functionality for task views
 */

// Detect if user is on a mobile device
function isMobileDevice() {
  return (
    window.innerWidth < 768 ||
    "ontouchstart" in window ||
    navigator.maxTouchPoints > 0 ||
    navigator.msMaxTouchPoints > 0
  );
}

// Format dates in a user-friendly way
function formatDate(dateString) {
  if (!dateString) return "";

  const date = new Date(dateString);
  const now = new Date();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);

  // Check if date is today or yesterday
  if (date.toDateString() === now.toDateString()) {
    return "Today";
  } else if (date.toDateString() === yesterday.toDateString()) {
    return "Yesterday";
  }

  // For other dates, format as Month Day, Year
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// Show toast notification
function showToast(message, type = "info", duration = 3000) {
  // Create toast element
  const toast = document.createElement("div");
  toast.className = `alert alert-${type} position-fixed`;
  toast.style.cssText =
    "top: 20px; right: 20px; z-index: 10000; min-width: 300px; max-width: 90%;";
  toast.innerHTML = `
    ${message}
    <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
  `;
  document.body.appendChild(toast);

  // Auto-remove after duration
  setTimeout(() => {
    if (toast.parentElement) {
      toast.remove();
    }
  }, duration);
}

// Format task priority with appropriate styles
function formatPriority(priority) {
  const priorityMap = {
    high: { class: "badge bg-danger", icon: "exclamation-circle" },
    medium: { class: "badge bg-warning text-dark", icon: "exclamation" },
    low: { class: "badge bg-success", icon: "check" },
  };

  const defaultPriority = { class: "badge bg-secondary", icon: "dash" };
  const p = priorityMap[priority.toLowerCase()] || defaultPriority;

  return `<span class="${p.class}"><i class="fas fa-${p.icon} me-1"></i>${priority}</span>`;
}

// Format task status with appropriate styles
function formatStatus(status) {
  const statusMap = {
    not_started: { class: "badge bg-secondary", text: "Not Started" },
    in_progress: { class: "badge bg-primary", text: "In Progress" },
    completed: { class: "badge bg-success", text: "Completed" },
    blocked: { class: "badge bg-danger", text: "Blocked" },
    review: { class: "badge bg-info", text: "Under Review" },
  };

  const defaultStatus = { class: "badge bg-secondary", text: status };
  const s = statusMap[status.toLowerCase()] || defaultStatus;

  return `<span class="${s.class}">${s.text}</span>`;
}

// Generate initials from a name
function getInitials(name) {
  if (!name) return "";
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .substring(0, 2);
}
