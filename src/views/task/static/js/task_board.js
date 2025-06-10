// Task Board JavaScript - Board View Functionality
document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on a mobile device
  const isMobile = isMobileDevice(); // Check if dragula is loaded
  if (typeof dragula === "undefined") {
    alert(
      "⚠️ Drag and drop functionality is not available. Please refresh the page."
    );
    return;
  }

  // Get all task container elements
  const containers = [
    document.getElementById("todo-tasks"),
    document.getElementById("in-progress-tasks"),
    document.getElementById("review-tasks"),
    document.getElementById("done-tasks"),
  ];
  // Filter out null containers
  const validContainers = containers.filter((c) => c !== null);
  if (validContainers.length === 0) {
    alert(
      "⚠️ Task board is not properly initialized. Please refresh the page."
    );
    return;
  }

  // Add click event to all task cards to show details
  addTaskCardClickListeners(); // Initialize Dragula for drag and drop functionality
  try {
    const drake = dragula(validContainers, {
      moves: function (el, source, handle, sibling) {
        return el && el.classList.contains("task-card");
      },
      accepts: function (el, target, source, sibling) {
        return target && target.classList.contains("task-column-tasks");
      },
      direction: "vertical",
      copy: false,
      copySortSource: false,
      revertOnSpill: true,
      removeOnSpill: false,
    });

    // Handle drop event
    drake.on("drop", function (el, target, source, sibling) {
      const taskId = el.getAttribute("data-task-id");
      const sourceColumn = source
        .closest(".task-column")
        .getAttribute("data-status");
      const targetColumn = target
        .closest(".task-column")
        .getAttribute("data-status");

      if (sourceColumn !== targetColumn) {
        // Update task count in columns
        updateTaskCount(sourceColumn, -1);
        updateTaskCount(targetColumn, 1);

        // Show success message
        showToast(
          `Task moved from ${getColumnDisplayName(
            sourceColumn
          )} to ${getColumnDisplayName(targetColumn)}`,
          "success"
        );
      }
    });

    // Add visual feedback during drag
    drake.on("drag", function (el, source) {
      el.classList.add("dragging");
      document.body.classList.add("dragging-active");
    });

    drake.on("dragend", function (el) {
      el.classList.remove("dragging");
      document.body.classList.remove("dragging-active");

      // Remove any drag-over classes
      document.querySelectorAll(".task-column").forEach((column) => {
        column.classList.remove("drag-over");
      });
    });

    drake.on("over", function (el, container, source) {
      if (container && container.closest) {
        container.closest(".task-column").classList.add("drag-over");
      }
    });

    drake.on("out", function (el, container, source) {
      if (container && container.closest) {
        container.closest(".task-column").classList.remove("drag-over");
      }
    });
  } catch (error) {
    alert(
      "⚠️ Drag and drop functionality could not be initialized. Please refresh the page."
    );
  }
  // Task click handler is handled by addTaskCardClickListeners()
  // Mobile-specific enhancements
  if (isMobile) {
    // Enable swipe gestures for task cards
    const taskCards = document.querySelectorAll(".task-card");
    let touchStartX = 0;
    let touchEndX = 0;
    let touchStartY = 0;
    let touchEndY = 0;
    let isCardSwiping = false;

    taskCards.forEach((card) => {
      card.addEventListener(
        "touchstart",
        (e) => {
          touchStartX = e.changedTouches[0].screenX;
          touchStartY = e.changedTouches[0].screenY; // Track Y to detect horizontal vs vertical swipe
          isCardSwiping = true;
        },
        { passive: true }
      );

      card.addEventListener(
        "touchmove",
        (e) => {
          if (!isCardSwiping) return;

          // Prevent container scrolling while swiping task cards
          const dx = e.changedTouches[0].screenX - touchStartX;
          const dy = e.changedTouches[0].screenY - touchStartY;

          // If primarily horizontal swipe and significant movement, prevent parent scrolling
          if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 30) {
            e.stopPropagation();
          }
        },
        { passive: false }
      );

      card.addEventListener(
        "touchend",
        (e) => {
          touchEndX = e.changedTouches[0].screenX;
          touchEndY = e.changedTouches[0].screenY;
          handleSwipe(card);
          isCardSwiping = false;
        },
        { passive: true }
      );
    });

    function handleSwipe(card) {
      const swipeDistance = touchEndX - touchStartX;
      const verticalDistance = Math.abs(touchEndY - touchStartY);

      // Only process if horizontal swipe is dominant
      if (
        Math.abs(swipeDistance) > verticalDistance &&
        Math.abs(swipeDistance) > 100
      ) {
        const taskId = card.getAttribute("data-task-id");
        const currentStatus = card
          .closest(".task-column")
          .getAttribute("data-status");
        let targetStatus = "";
        if (swipeDistance > 0) {
          // Right swipe - move to previous column
          targetStatus = getPreviousStatus(currentStatus);
        } else {
          // Left swipe - move to next column
          targetStatus = getNextStatus(currentStatus);
        }

        // Only proceed if we found a valid target status
        if (targetStatus) {
          moveTaskToColumn(card, taskId, currentStatus, targetStatus);
        }
      }
    }

    // Helper to find next column status
    function getNextStatus(currentStatus) {
      const statusOrder = ["todo", "in_progress", "review", "done"];
      const currentIndex = statusOrder.indexOf(currentStatus);

      if (currentIndex < statusOrder.length - 1) {
        return statusOrder[currentIndex + 1];
      }
      return "";
    }

    // Helper to find previous column status
    function getPreviousStatus(currentStatus) {
      const statusOrder = ["todo", "in_progress", "review", "done"];
      const currentIndex = statusOrder.indexOf(currentStatus);

      if (currentIndex > 0) {
        return statusOrder[currentIndex - 1];
      }
      return "";
    }

    // Move task card to a different column
    function moveTaskToColumn(card, taskId, sourceStatus, targetStatus) {
      const targetColumn = document.querySelector(
        `[data-status="${targetStatus}"] .task-column-tasks`
      );

      if (!targetColumn) return;

      // Move the card to the target column
      targetColumn.appendChild(card);

      // Update task counts
      updateTaskCount(sourceStatus, -1);
      updateTaskCount(targetStatus, 1);

      // Show success message
      showToast(
        `Task moved from ${getColumnDisplayName(
          sourceStatus
        )} to ${getColumnDisplayName(targetStatus)}`,
        "success"
      );

      // Scroll to show the target column
      const taskBoard = document.querySelector(".task-board");
      if (taskBoard) {
        const targetColumnElement = targetColumn.closest(".task-column");
        taskBoard.scrollTo({
          left: targetColumnElement.offsetLeft - 20,
          behavior: "smooth",
        });
      }
    }
  }

  // Helper functions
  function updateTaskCount(columnStatus, change) {
    const column = document.querySelector(
      `[data-status="${columnStatus}"] .task-count`
    );
    if (column) {
      const currentCount = parseInt(column.textContent) || 0;
      column.textContent = Math.max(0, currentCount + change);
    }
  }

  function getColumnDisplayName(status) {
    const names = {
      todo: "To Do",
      in_progress: "In Progress",
      review: "Review",
      done: "Done",
    };
    return names[status] || status;
  }
  // Using the common showToast function from task_common.js
  // Use fetchTaskDetails instead of openTaskDetailModal

  // Helper functions
  function isMobileDevice() {
    return window.innerWidth < 768 || "ontouchstart" in window;
  }
  // Function to make API requests with authentication handling
  async function apiRequest(url, method = "GET", data = null) {
    return await authenticatedApiRequest(url, method, data);
  } // Function to add click event listeners to task cards
  function addTaskCardClickListeners() {
    const taskCards = document.querySelectorAll(".task-card");

    taskCards.forEach((card) => {
      card.addEventListener("click", function (e) {
        // Don't trigger click during drag operations
        if (
          this.classList.contains("gu-mirror") ||
          this.classList.contains("gu-transit")
        ) {
          return;
        }

        const taskId = this.getAttribute("data-task-id");
        if (taskId) {
          fetchTaskDetails(taskId);
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

  // Ẩn filter row nếu có (nếu bạn có filter row cũ, thêm class d-none d-md-block để chỉ hiện trên desktop)
  // Xử lý filter mobile
  const filterFormMobile = document.getElementById("taskFilterFormMobile");
  if (filterFormMobile) {
    filterFormMobile.addEventListener("submit", function (e) {
      e.preventDefault();
      // Lấy giá trị filter
      const project = document.getElementById("projectFilterMobile").value;
      const assignee = document.getElementById("assigneeFilterMobile").value;
      const priority = document.getElementById("priorityFilterMobile").value;
      const dueDate = document.getElementById("dueDateFilterMobile").value;

      // Build query string
      const params = new URLSearchParams();
      if (project) params.append("project", project);
      if (assignee) params.append("assignee", assignee);
      if (priority) params.append("priority", priority);
      if (dueDate) params.append("due_date", dueDate);

      // Redirect with filters
      const queryString = params.toString();
      if (queryString) {
        window.location.href = `/tasks?${queryString}`;
      } else {
        window.location.href = "/tasks";
      }
    });
  }
});
