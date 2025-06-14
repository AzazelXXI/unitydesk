document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on a mobile device
  const isMobile = isMobileDevice();
  // Check if we're on a small screen (regardless of device type)
  const isSmallScreen = window.innerWidth < 768;

  // Add click event listeners to task rows for showing details
  addTaskRowClickListeners();

  // Task checkboxes
  document
    .querySelectorAll('input[type="checkbox"]')
    .forEach(function (checkbox) {
      checkbox.addEventListener("change", function () {
        const row = this.closest("tr");
        if (this.checked) {
          row.style.opacity = "0.6";
        } else {
          row.style.opacity = "1";
        }
      });
    });

  // Helper function to adjust layout based on screen size
  function adjustLayout() {
    const isNowSmallScreen = window.innerWidth < 768;

    // Handle responsive table
    const table = document.querySelector(".table");
    if (table) {
      // Always make sure table is responsive
      if (!table.parentElement.classList.contains("table-responsive")) {
        const wrapper = document.createElement("div");
        wrapper.className = "table-responsive";
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      }

      // Hide/show columns based on screen size
      const projectCol = document.querySelectorAll(
        "th:nth-child(3), td:nth-child(3)"
      );
      const dueDateCol = document.querySelectorAll(
        "th:nth-child(6), td:nth-child(6)"
      );

      if (isNowSmallScreen) {
        projectCol.forEach((cell) => cell.classList.add("mobile-hide"));
        dueDateCol.forEach((cell) => cell.classList.add("mobile-hide"));
      } else {
        projectCol.forEach((cell) => cell.classList.remove("mobile-hide"));
        dueDateCol.forEach((cell) => cell.classList.remove("mobile-hide"));
      }
    }
  }

  // Mobile-specific enhancements
  if (isMobile || isSmallScreen) {
    // Create filter toggle for small screens
    const filterSection = document.querySelector(".task-filter-section");
    if (filterSection) {
      const filterRow = document.querySelector(".row.g-3");
      if (filterRow) {
        filterRow.classList.add("task-filter-row");

        // Create toggle button
        const toggleButton = document.createElement("div");
        toggleButton.className = "task-filter-toggle";
        toggleButton.innerHTML = 'Filters <i class="fas fa-chevron-down"></i>';

        // Insert toggle before the filter row
        filterSection.insertBefore(toggleButton, filterRow);

        // Add click handler for toggle
        toggleButton.addEventListener("click", function () {
          filterRow.classList.toggle("expanded");
          const icon = this.querySelector("i");
          if (filterRow.classList.contains("expanded")) {
            icon.className = "fas fa-chevron-up";
          } else {
            icon.className = "fas fa-chevron-down";
          }
        });
      }
    }

    // Run initial layout adjustment
    adjustLayout();
  }
  // Listen for window resize events to adjust responsive behavior
  window.addEventListener("resize", adjustLayout);
  // Function to add click event listeners to task rows
  function addTaskRowClickListeners() {
    const taskRows = document.querySelectorAll(".task-row");

    taskRows.forEach((row) => {
      const taskId = row.getAttribute("data-task-id");

      row.addEventListener("click", function (e) {
        // Don't trigger click if clicking on checkboxes or action buttons
        if (e.target.type === "checkbox" || e.target.closest(".dropdown")) {
          return;
        }

        const clickedTaskId = this.getAttribute("data-task-id");

        if (clickedTaskId) {
          fetchTaskDetails(clickedTaskId);
        }
      });
    });
  }
  // Function to fetch task details and populate modal
  function fetchTaskDetails(taskId) {
    // Show loading state
    const taskDetailContent = document.getElementById("taskDetailContent");
    if (!taskDetailContent) {
      alert("⚠️ Task detail modal is not available. Please refresh the page.");
      return;
    }

    taskDetailContent.innerHTML =
      '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><div class="mt-2">Loading task details...</div></div>';

    // Initialize Bootstrap modal
    const taskDetailModalElement = document.getElementById("taskDetailModal");
    if (!taskDetailModalElement) {
      alert("⚠️ Task detail modal is not available. Please refresh the page.");
      return;
    }
    const taskDetailModal = new bootstrap.Modal(taskDetailModalElement);
    taskDetailModal.show(); // Fetch task details from API with authentication handling
    fetch(`/api/simple-tasks/${taskId}`, {
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    })
      .then((response) => {
        // Check for authentication errors
        if (response.status === 401 || response.status === 403) {
          // Clear any existing authentication data
          document.cookie =
            "remember_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";

          // Show user-friendly message
          showToast(
            "Your session has expired. Please log in again.",
            "warning",
            2000
          );

          // Redirect to login page after a short delay
          setTimeout(() => {
            window.location.href = "/login";
          }, 2000);

          throw new Error("Authentication failed");
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
      })
      .then((task) => {
        populateTaskDetailModal(task);
      })
      .catch((error) => {
        // Error handling
        if (!error.message.includes("Authentication failed")) {
          taskDetailContent.innerHTML = `<div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>Unable to load task details. Please try again later.
          </div>`;
        }
      });
  }

  // Function to populate the modal with task details
  function populateTaskDetailModal(task) {
    const detailContent = document.getElementById("taskDetailContent");

    // Handle different API response formats
    const taskData = {
      id: task.id,
      title: task.title || task.name || `Task ${task.id}`,
      description: task.description || "No description provided",
      status: task.status || "unknown",
      priority: task.priority || "medium",
      due_date: task.due_date || null,
      created_at: task.created_at || null,
      assignee: task.assignee || { name: "Unassigned", initials: "?" },
      project: task.project || { name: "Unknown Project" },
    };

    // Format dates
    const dueDate = taskData.due_date
      ? new Date(taskData.due_date).toLocaleDateString()
      : "No due date";
    const createdDate = taskData.created_at
      ? new Date(taskData.created_at).toLocaleDateString()
      : "Unknown";

    // Determine status badge class
    let statusBadgeClass = "";
    const status = String(taskData.status).toLowerCase();
    switch (status) {
      case "todo":
      case "not_started":
      case "pending":
        statusBadgeClass = "bg-secondary";
        break;
      case "in_progress":
      case "active":
      case "working":
        statusBadgeClass = "bg-primary";
        break;
      case "review":
      case "blocked":
        statusBadgeClass = "bg-warning";
        break;
      case "done":
      case "completed":
      case "finished":
        statusBadgeClass = "bg-success";
        break;
      default:
        statusBadgeClass = "bg-secondary";
    }

    // Determine priority badge class
    let priorityBadgeClass = "";
    const priority = String(taskData.priority).toLowerCase();
    switch (priority) {
      case "high":
        priorityBadgeClass = "bg-danger";
        break;
      case "medium":
        priorityBadgeClass = "bg-warning";
        break;
      case "low":
        priorityBadgeClass = "bg-success";
        break;
      default:
        priorityBadgeClass = "bg-secondary";
    }

    // Format status and priority for display
    const statusDisplay = String(taskData.status)
      .replace(/[_-]/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    const priorityDisplay =
      String(taskData.priority).charAt(0).toUpperCase() +
      String(taskData.priority).slice(1);

    // Create HTML for task details
    detailContent.innerHTML = `
      <div class="task-detail">
        <h3>${taskData.title}</h3>
        <div class="row mb-4">
          <div class="col-md-6 mb-2">
            <span class="badge ${statusBadgeClass}">${statusDisplay}</span>
            <span class="badge ${priorityBadgeClass} ms-2">${priorityDisplay}</span>
          </div>
          <div class="col-md-6 text-md-end">
            <small class="text-muted">Created: ${createdDate}</small>
          </div>
        </div>
        
        <div class="card mb-4">
          <div class="card-header">
            <i class="fas fa-align-left me-2"></i>Description
          </div>
          <div class="card-body">
            <p class="card-text">${taskData.description}</p>
          </div>
        </div>
        
        <div class="row mb-3">
          <div class="col-md-6">
            <div class="card mb-3">
              <div class="card-header">
                <i class="fas fa-calendar me-2"></i>Due Date
              </div>
              <div class="card-body">
                <p class="card-text">${dueDate}</p>
              </div>
            </div>
          </div>          <div class="col-md-6">
            <div class="card mb-3">
              <div class="card-header d-flex justify-content-between align-items-center">
                <span><i class="fas fa-user me-2"></i>Assigned To</span>
                <button type="button" class="btn btn-sm btn-outline-primary" id="changeAssigneeBtn">
                  <i class="fas fa-edit me-1"></i>Change
                </button>
              </div>
              <div class="card-body">
                <div class="d-flex align-items-center" id="currentAssigneeDisplay">
                  <div class="assignee-avatar me-2">
                    ${
                      taskData.assignee.initials ||
                      taskData.assignee.name?.charAt(0) ||
                      "?"
                    }
                  </div>
                  <span>${taskData.assignee.name || "Unassigned"}</span>
                </div>
                <div class="d-none" id="assigneeChangeForm">
                  <div class="mb-2">
                    <select class="form-select form-select-sm" id="assigneeSelect">
                      <option value="">Select Assignee</option>
                    </select>
                  </div>
                  <div class="d-flex gap-2">
                    <button type="button" class="btn btn-sm btn-success" id="saveAssigneeBtn">
                      <i class="fas fa-check me-1"></i>Save
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary" id="cancelAssigneeBtn">
                      <i class="fas fa-times me-1"></i>Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="card mb-3">
          <div class="card-header">
            <i class="fas fa-project-diagram me-2"></i>Project
          </div>
          <div class="card-body">
            <p class="card-text">${
              taskData.project.name || "Unknown Project"
            }</p>
          </div>
        </div>
      </div>
    `; // Set the task ID on the edit button
    const editTaskBtn = document.getElementById("editTaskBtn");
    if (editTaskBtn) {
      editTaskBtn.setAttribute("data-task-id", taskData.id);

      // Add click handler for edit button
      editTaskBtn.onclick = function () {
        // Check if there's an edit route available
        const editUrl = `/tasks/${taskData.id}/edit`;
        window.location.href = editUrl;
      };
    }

    // Initialize assignment functionality
    setupTaskAssignmentHandlers(taskData);
  }

  // Function to setup task assignment handlers
  function setupTaskAssignmentHandlers(taskData) {
    const changeAssigneeBtn = document.getElementById("changeAssigneeBtn");
    const assigneeChangeForm = document.getElementById("assigneeChangeForm");
    const currentAssigneeDisplay = document.getElementById(
      "currentAssigneeDisplay"
    );
    const saveAssigneeBtn = document.getElementById("saveAssigneeBtn");
    const cancelAssigneeBtn = document.getElementById("cancelAssigneeBtn");
    const assigneeSelect = document.getElementById("assigneeSelect");

    if (!changeAssigneeBtn || !assigneeChangeForm || !currentAssigneeDisplay) {
      return;
    }

    // Load users for assignment dropdown
    loadUsersForAssignment();

    // Show assignment form
    changeAssigneeBtn.addEventListener("click", function () {
      currentAssigneeDisplay.classList.add("d-none");
      assigneeChangeForm.classList.remove("d-none");

      // Set current assignee as selected
      if (taskData.assignee && taskData.assignee.id) {
        assigneeSelect.value = taskData.assignee.id;
      }
    });

    // Cancel assignment change
    cancelAssigneeBtn.addEventListener("click", function () {
      currentAssigneeDisplay.classList.remove("d-none");
      assigneeChangeForm.classList.add("d-none");
    });

    // Save assignment change
    saveAssigneeBtn.addEventListener("click", function () {
      const newAssigneeId = assigneeSelect.value;
      updateTaskAssignment(taskData.id, newAssigneeId);
    });
  }

  // Function to load users for assignment dropdown
  async function loadUsersForAssignment() {
    try {
      const response = await fetch("/api/simple-tasks/users", {
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const users = await response.json();
      const assigneeSelect = document.getElementById("assigneeSelect");

      if (assigneeSelect) {
        // Clear existing options except the first one
        assigneeSelect.innerHTML = '<option value="">Select Assignee</option>';

        // Add user options
        users.forEach((user) => {
          const option = document.createElement("option");
          option.value = user.id;
          option.textContent =
            user.profile?.display_name || user.name || user.email;
          assigneeSelect.appendChild(option);
        });
      }
    } catch (error) {
      console.error("Error loading users:", error);
      showToast("Failed to load users for assignment", "error");
    }
  }

  // Function to update task assignment
  async function updateTaskAssignment(taskId, newAssigneeId) {
    try {
      const response = await fetch(`/api/simple-tasks/${taskId}/assign`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          assignee_id: newAssigneeId || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const updatedTask = await response.json();

      // Update the display
      updateAssigneeDisplay(updatedTask);

      // Hide the form and show the display
      const currentAssigneeDisplay = document.getElementById(
        "currentAssigneeDisplay"
      );
      const assigneeChangeForm = document.getElementById("assigneeChangeForm");

      if (currentAssigneeDisplay && assigneeChangeForm) {
        currentAssigneeDisplay.classList.remove("d-none");
        assigneeChangeForm.classList.add("d-none");
      }

      showToast("Task assignment updated successfully", "success");

      // Reload the page to reflect changes in the task list
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      console.error("Error updating task assignment:", error);
      showToast("Failed to update task assignment", "error");
    }
  }

  // Function to update assignee display
  function updateAssigneeDisplay(taskData) {
    const currentAssigneeDisplay = document.getElementById(
      "currentAssigneeDisplay"
    );

    if (currentAssigneeDisplay) {
      const assigneeInitials =
        taskData.assignee?.initials ||
        taskData.assignee?.name?.charAt(0) ||
        "?";
      const assigneeName = taskData.assignee?.name || "Unassigned";

      currentAssigneeDisplay.innerHTML = `
        <div class="assignee-avatar me-2">${assigneeInitials}</div>
        <span>${assigneeName}</span>
      `;
    }
  }

  // Function to show toast messages (if not already available)
  function showToast(message, type = "info", duration = 3000) {
    // Create toast element if it doesn't exist
    let toastContainer = document.querySelector(".toast-container");
    if (!toastContainer) {
      toastContainer = document.createElement("div");
      toastContainer.className =
        "toast-container position-fixed top-0 end-0 p-3";
      document.body.appendChild(toastContainer);
    }

    const toastId = "toast-" + Date.now();
    const toastHtml = `
      <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header">
          <strong class="me-auto text-${type === "error" ? "danger" : type}">${
      type === "error" ? "Error" : "Success"
    }</strong>
          <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">${message}</div>
      </div>
    `;

    toastContainer.insertAdjacentHTML("beforeend", toastHtml);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    // Remove toast after duration
    setTimeout(() => {
      if (toastElement) {
        toastElement.remove();
      }
    }, duration + 1000);
  }

  // Helper function to check if we're on a mobile device
  function isMobileDevice() {
    return window.innerWidth < 768 || "ontouchstart" in window;
  }
});
