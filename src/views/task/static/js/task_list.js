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
    console.log(`Found ${taskRows.length} task rows for click listeners`);

    taskRows.forEach((row, index) => {
      const taskId = row.getAttribute("data-task-id");
      console.log(`Task row ${index}: ID = ${taskId}`);
      
      row.addEventListener("click", function (e) {
        // Don't trigger click if clicking on checkboxes or action buttons
        if (e.target.type === "checkbox" || e.target.closest(".dropdown")) {
          return;
        }

        const clickedTaskId = this.getAttribute("data-task-id");
        
        // SIMPLE TEST: Show alert to verify click is working
        alert(`✅ List View Click detected! Task ID: ${clickedTaskId}`);
        
        console.log("Task row clicked:", clickedTaskId);

        if (clickedTaskId) {
          // Comment out the modal for now to test just the click
          // fetchTaskDetails(clickedTaskId);
          console.log("Would fetch task details for:", clickedTaskId);
        }
      });
    });
  }

  // Function to fetch task details and populate modal
  function fetchTaskDetails(taskId) {
    // Show loading state
    const taskDetailContent = document.getElementById("taskDetailContent");
    taskDetailContent.innerHTML =
      '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><div class="mt-2">Loading task details...</div></div>';

    // Initialize Bootstrap modal
    const taskDetailModal = new bootstrap.Modal(
      document.getElementById("taskDetailModal")
    );
    taskDetailModal.show();    // Try different API endpoints for task details
    const endpoints = [
      `/api/tasks/${taskId}`, // This should work now with our simple_task_api
      `/api/v1/api/tasks/${taskId}`, // API v1 endpoint
      `/tasks/${taskId}/api`, // fallback if needed
    ];

    async function tryFetchTask(endpointIndex = 0) {
      if (endpointIndex >= endpoints.length) {
        // All endpoints failed, show error
        taskDetailContent.innerHTML = `<div class="alert alert-danger">
          <i class="fas fa-exclamation-triangle me-2"></i>Unable to load task details. Please try again later.
        </div>`;
        return;
      }

      try {
        const response = await fetch(endpoints[endpointIndex], {
          headers: {
            Accept: "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
          credentials: "same-origin",
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const task = await response.json();
        populateTaskDetailModal(task);
      } catch (error) {
        console.warn(`Endpoint ${endpoints[endpointIndex]} failed:`, error);
        // Try next endpoint
        tryFetchTask(endpointIndex + 1);
      }
    }

    tryFetchTask();
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
          </div>
          <div class="col-md-6">
            <div class="card mb-3">
              <div class="card-header">
                <i class="fas fa-user me-2"></i>Assigned To
              </div>
              <div class="card-body">
                <div class="d-flex align-items-center">
                  <div class="assignee-avatar me-2">
                    ${
                      taskData.assignee.initials ||
                      taskData.assignee.name?.charAt(0) ||
                      "?"
                    }
                  </div>
                  <span>${taskData.assignee.name || "Unassigned"}</span>
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
    `;

    // Set the task ID on the edit button
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
  }

  // Helper function to check if we're on a mobile device
  function isMobileDevice() {
    return window.innerWidth < 768 || "ontouchstart" in window;
  }
});
