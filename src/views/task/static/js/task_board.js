document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM Content Loaded");

  // Check if we're on a mobile device
  const isMobile = isMobileDevice();

  // Check if dragula is loaded
  if (typeof dragula === "undefined") {
    console.error("Dragula library not loaded!");
    return;
  }

  console.log("Dragula library loaded successfully");
  console.log("Initializing drag and drop...");

  // Get all task container elements
  const containers = [
    document.getElementById("todo-tasks"),
    document.getElementById("in-progress-tasks"),
    document.getElementById("review-tasks"),
    document.getElementById("done-tasks"),
  ];

  // Check if containers exist
  console.log(
    "Containers found:",
    containers.map((c) => (c ? c.id : "null"))
  );

  // Filter out null containers
  const validContainers = containers.filter((c) => c !== null);

  if (validContainers.length === 0) {
    console.error("No valid containers found for drag and drop");
    return;
  }

  console.log("Valid containers:", validContainers.length);

  // Add click event to all task cards to show details
  addTaskCardClickListeners();

  // Initialize Dragula
  try {
    const drake = dragula(validContainers, {
      moves: function (el, source, handle, sibling) {
        const canMove = el && el.classList.contains("task-card");
        console.log("Can move element:", canMove, el);
        return canMove;
      },
      accepts: function (el, target, source, sibling) {
        const canAccept =
          target && target.classList.contains("task-column-tasks");
        console.log("Can accept in target:", canAccept, target);
        return canAccept;
      },
      direction: "vertical",
      copy: false,
      copySortSource: false,
      revertOnSpill: true,
      removeOnSpill: false,
    });
    console.log("Dragula initialized successfully");

    // Handle drop event
    drake.on("drop", function (el, target, source, sibling) {
      console.log("Drop event triggered");
      const taskId = el.getAttribute("data-task-id");
      const sourceColumn = source
        .closest(".task-column")
        .getAttribute("data-status");
      const targetColumn = target
        .closest(".task-column")
        .getAttribute("data-status");

      console.log(
        `Moving task ${taskId} from ${sourceColumn} to ${targetColumn}`
      );

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
      console.log("Drag started for task:", el.getAttribute("data-task-id"));
      el.classList.add("dragging");
      document.body.classList.add("dragging-active");
    });

    drake.on("dragend", function (el) {
      console.log("Drag ended");
      el.classList.remove("dragging");
      document.body.classList.remove("dragging-active");

      // Remove any drag-over classes
      document.querySelectorAll(".task-column").forEach((column) => {
        column.classList.remove("drag-over");
      });
    });

    drake.on("over", function (el, container, source) {
      console.log("Drag over container");
      if (container && container.closest) {
        container.closest(".task-column").classList.add("drag-over");
      }
    });

    drake.on("out", function (el, container, source) {
      console.log("Drag out of container");
      if (container && container.closest) {
        container.closest(".task-column").classList.remove("drag-over");
      }
    });

    console.log("All drag and drop events registered");
  } catch (error) {
    console.error("Error initializing dragula:", error);
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
          console.log("Right swipe detected");
          targetStatus = getPreviousStatus(currentStatus);
        } else {
          // Left swipe - move to next column
          console.log("Left swipe detected");
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

  // Function to make API requests
  async function apiRequest(url, method = "GET", data = null) {
    try {
      const options = {
        method: method,
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      };

      if (
        data &&
        (method === "POST" || method === "PUT" || method === "PATCH")
      ) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(url, options);

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      // For DELETE requests or others that may not return content
      if (
        response.status === 204 ||
        response.headers.get("Content-Length") === "0"
      ) {
        return true;
      }

      return await response.json();
    } catch (error) {
      console.error("API request error:", error);
      throw error;
    }
  }

  // Function to add click event listeners to task cards
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
    taskDetailContent.innerHTML =
      '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"></div><div class="mt-2">Loading task details...</div></div>';

    // Initialize Bootstrap modal
    const taskDetailModal = new bootstrap.Modal(
      document.getElementById("taskDetailModal")
    );
    taskDetailModal.show();

    // Fetch the task details
    fetch(`/api/v1/tasks/${taskId}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((task) => {
        // Once we have the task data, populate the modal
        populateTaskDetailModal(task);
      })
      .catch((error) => {
        console.error("Error fetching task details:", error);
        taskDetailContent.innerHTML = `<div class="alert alert-danger">
          <i class="fas fa-exclamation-triangle me-2"></i>Error loading task details. Please try again.
        </div>`;
      });
  }

  // Function to populate the modal with task details
  function populateTaskDetailModal(task) {
    const detailContent = document.getElementById("taskDetailContent");

    // Format dates
    const dueDate = new Date(task.due_date).toLocaleDateString();
    const createdDate = new Date(task.created_at).toLocaleDateString();

    // Determine status badge class
    let statusBadgeClass = "";
    switch (task.status) {
      case "todo":
        statusBadgeClass = "bg-secondary";
        break;
      case "in_progress":
        statusBadgeClass = "bg-primary";
        break;
      case "review":
        statusBadgeClass = "bg-warning";
        break;
      case "done":
        statusBadgeClass = "bg-success";
        break;
      default:
        statusBadgeClass = "bg-secondary";
    }

    // Determine priority badge class
    let priorityBadgeClass = "";
    switch (task.priority) {
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
    const statusDisplay = task.status
      .replace("_", " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    const priorityDisplay =
      task.priority.charAt(0).toUpperCase() + task.priority.slice(1);

    // Create HTML for task details
    detailContent.innerHTML = `
      <div class="task-detail">
        <h3>${task.title}</h3>
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
            <p class="card-text">${
              task.description || "No description provided."
            }</p>
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
                    ${task.assignee.initials}
                  </div>
                  <span>${task.assignee.name}</span>
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
            <p class="card-text">${task.project.name}</p>
          </div>
        </div>
      </div>
    `;

    // Set the task ID on the edit button
    const editTaskBtn = document.getElementById("editTaskBtn");
    editTaskBtn.setAttribute("data-task-id", task.id);

    // Add click handler for edit button
    editTaskBtn.onclick = function () {
      window.location.href = `/tasks/edit/${task.id}`;
    };
  }
});
