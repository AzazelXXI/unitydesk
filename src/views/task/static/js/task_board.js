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
    }); // Handle drop event
    drake.on("drop", function (el, target, source, sibling) {
      const taskId = el.getAttribute("data-task-id");
      const sourceColumn = source
        .closest(".task-column")
        .getAttribute("data-status");
      const targetColumn = target
        .closest(".task-column")
        .getAttribute("data-status");

      if (sourceColumn !== targetColumn) {
        // Update task status in database
        updateTaskStatus(taskId, targetColumn, sourceColumn)
          .then(() => {
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
          })
          .catch((error) => {
            // If update fails, revert the visual change
            console.error("Failed to update task status:", error);

            // Move the card back to source column
            source.appendChild(el);

            showToast(`Failed to move task. Please try again.`, "error");
          });
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
    } // Move task card to a different column
    function moveTaskToColumn(card, taskId, sourceStatus, targetStatus) {
      const targetColumn = document.querySelector(
        `[data-status="${targetStatus}"] .task-column-tasks`
      );

      if (!targetColumn) return;

      // Update task status in database first
      updateTaskStatus(taskId, targetStatus, sourceStatus)
        .then(() => {
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
        })
        .catch((error) => {
          console.error("Failed to update task status:", error);
          showToast(`Failed to move task. Please try again.`, "error");
        });
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

  // Function to update task status in database
  async function updateTaskStatus(taskId, newStatus, oldStatus) {
    try {
      // Map column status to database status values
      const statusMapping = {
        todo: "NOT_STARTED",
        in_progress: "IN_PROGRESS",
        review: "UNDER_REVIEW",
        done: "COMPLETED",
      };

      const dbStatus = statusMapping[newStatus];
      if (!dbStatus) {
        throw new Error(`Invalid status: ${newStatus}`);
      }

      console.log(
        `🔄 Updating task ${taskId} status from ${oldStatus} to ${newStatus} (${dbStatus})`
      );

      const response = await fetch(`/api/simple-tasks/${taskId}/status`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          status: dbStatus,
        }),
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          handleAuthenticationError();
          return;
        }

        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      console.log("✅ Task status updated successfully:", result);

      return result;
    } catch (error) {
      console.error("❌ Error updating task status:", error);
      throw error;
    }
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
        </div>        <div class="card mb-3">
          <div class="card-header">
            <i class="fas fa-project-diagram me-2"></i>Project
          </div>
          <div class="card-body">
            <p class="card-text">${
              taskData.project.name || "Unknown Project"
            }</p>
          </div>
        </div>

        <!-- Attachments Section -->
        <div class="card mb-3">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span><i class="fas fa-paperclip me-2"></i>Attachments</span>
            <span class="badge bg-secondary" id="attachmentsCount">0</span>
          </div>
          <div class="card-body">
            <!-- Upload Attachment Form -->
            <div class="mb-3">
              <div class="d-flex align-items-center">
                <input 
                  type="file" 
                  class="form-control me-2" 
                  id="attachmentFile" 
                  multiple
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar"
                >
                <button 
                  type="button" 
                  class="btn btn-primary" 
                  id="uploadAttachmentBtn"
                  style="white-space: nowrap;"
                >
                  <i class="fas fa-upload me-1"></i>Upload
                </button>
              </div>
              <small class="text-muted">
                Supported: PDF, DOC, XLS, TXT, Images, ZIP (Max 10MB each)
              </small>
            </div>
            
            <!-- Attachments List -->
            <div id="attachmentsList">
              <div class="text-center text-muted py-3" id="noAttachmentsMessage">
                <i class="fas fa-file-slash me-2"></i>
                No attachments yet. Upload files to share with your team!
              </div>
            </div>
            
            <!-- Upload Progress -->
            <div class="d-none" id="uploadProgress">
              <div class="progress mb-2">
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
              </div>
              <small class="text-muted">Uploading...</small>
            </div>
            
            <!-- Loading State -->
            <div class="text-center py-3 d-none" id="attachmentsLoading">
              <div class="spinner-border spinner-border-sm text-primary me-2"></div>
              Loading attachments...
            </div>
          </div>
        </div>

        <!-- Comments Section -->
        <div class="card mb-3">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span><i class="fas fa-comments me-2"></i>Comments</span>
            <span class="badge bg-secondary" id="commentsCount">0</span>
          </div>
          <div class="card-body">
            <!-- Add Comment Form -->
            <div class="mb-3">
              <div class="d-flex">
                <textarea 
                  class="form-control me-2" 
                  id="newCommentText" 
                  rows="2" 
                  placeholder="Add a comment..."
                ></textarea>
                <button 
                  type="button" 
                  class="btn btn-primary" 
                  id="addCommentBtn"
                  style="height: fit-content;"
                >
                  <i class="fas fa-paper-plane"></i>
                </button>
              </div>
            </div>
            
            <!-- Comments List -->
            <div id="commentsList">
              <div class="text-center text-muted py-3" id="noCommentsMessage">
                <i class="fas fa-comment-slash me-2"></i>
                No comments yet. Be the first to add one!
              </div>
            </div>
            
            <!-- Loading State -->
            <div class="text-center py-3 d-none" id="commentsLoading">
              <div class="spinner-border spinner-border-sm text-primary me-2"></div>
              Loading comments...
            </div>
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
    } // Initialize assignment functionality
    setupTaskAssignmentHandlers(taskData);
    // Initialize attachments functionality
    console.log("🔗 Initializing attachments for task:", taskData.id);
    setupTaskAttachmentsHandlers(taskData.id);
    loadTaskAttachments(taskData.id);

    // Initialize comments functionality
    setupTaskCommentsHandlers(taskData.id);
    loadTaskComments(taskData.id);
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
  } // Function to load users for assignment dropdown
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

      // Reload the page to reflect changes in the task board
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

  // Function to show toast messages (if not already available from task_common.js)
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

  // Function to setup task comments handlers
  function setupTaskCommentsHandlers(taskId) {
    const addCommentBtn = document.getElementById("addCommentBtn");
    const newCommentText = document.getElementById("newCommentText");

    if (!addCommentBtn || !newCommentText) {
      return;
    }

    // Add comment button click handler
    addCommentBtn.addEventListener("click", async function () {
      const commentText = newCommentText.value.trim();
      if (!commentText) {
        showToast("Please enter a comment", "warning");
        return;
      }

      try {
        addCommentBtn.disabled = true;
        addCommentBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        await addTaskComment(taskId, commentText);
        newCommentText.value = "";
        await loadTaskComments(taskId);
        showToast("Comment added successfully", "success");
      } catch (error) {
        showToast("Failed to add comment", "error");
        console.error("Error adding comment:", error);
      } finally {
        addCommentBtn.disabled = false;
        addCommentBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
      }
    });

    // Add comment on Enter key (Ctrl+Enter for new line)
    newCommentText.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.ctrlKey) {
        e.preventDefault();
        addCommentBtn.click();
      }
    });
  }
  // Function to load task comments
  async function loadTaskComments(taskId) {
    const commentsList = document.getElementById("commentsList");
    const commentsCount = document.getElementById("commentsCount");
    const commentsLoading = document.getElementById("commentsLoading");
    const noCommentsMessage = document.getElementById("noCommentsMessage");

    if (!commentsList || !commentsCount) {
      return;
    }

    try {
      // Show loading state
      if (commentsLoading) commentsLoading.classList.remove("d-none");
      if (noCommentsMessage) noCommentsMessage.classList.add("d-none");

      const response = await fetch(`/api/simple-tasks/${taskId}/comments`, {
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      });

      // Handle authentication errors
      if (response.status === 401 || response.status === 403) {
        showToast("Your session has expired. Please log in again.", "warning");
        setTimeout(() => {
          window.location.href = "/login";
        }, 2000);
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const comments = await response.json();
      displayComments(comments);
      commentsCount.textContent = comments.length;
    } catch (error) {
      console.error("Error loading comments:", error);
      commentsList.innerHTML = `
        <div class="alert alert-warning">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Failed to load comments. Please try again.
        </div>
      `;
    } finally {
      if (commentsLoading) commentsLoading.classList.add("d-none");
    }
  }

  // Function to display comments
  function displayComments(comments) {
    const commentsList = document.getElementById("commentsList");
    const noCommentsMessage = document.getElementById("noCommentsMessage");

    if (!commentsList) return;

    if (comments.length === 0) {
      if (noCommentsMessage) noCommentsMessage.classList.remove("d-none");
      commentsList.innerHTML = `
        <div class="text-center text-muted py-3" id="noCommentsMessage">
          <i class="fas fa-comment-slash me-2"></i>
          No comments yet. Be the first to add one!
        </div>
      `;
      return;
    }

    if (noCommentsMessage) noCommentsMessage.classList.add("d-none");

    const commentsHtml = comments
      .map((comment) => {
        const createdDate = new Date(comment.created_at).toLocaleString();
        const userInitials =
          comment.user?.name?.charAt(0)?.toUpperCase() || "?";

        return `
        <div class="comment-item mb-3 p-3 border rounded">
          <div class="d-flex align-items-start">
            <div class="comment-avatar me-3">
              <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center" 
                   style="width: 40px; height: 40px; font-weight: bold;">
                ${userInitials}
              </div>
            </div>
            <div class="flex-grow-1">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <strong class="text-primary">${
                  comment.user?.name || "Unknown User"
                }</strong>
                <small class="text-muted">${createdDate}</small>
              </div>
              <div class="comment-content">
                ${comment.content.replace(/\n/g, "<br>")}
              </div>
            </div>
          </div>
        </div>
      `;
      })
      .join("");

    commentsList.innerHTML = commentsHtml;
  }
  // Function to add a task comment
  async function addTaskComment(taskId, content) {
    const response = await fetch(`/api/simple-tasks/${taskId}/comments`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify({
        content: content,
        // user_id is automatically set from current authenticated user
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  }
  // Function to setup task attachments handlers
  function setupTaskAttachmentsHandlers(taskId) {
    console.log("⚙️ Setting up attachment handlers for task:", taskId);
    const uploadAttachmentBtn = document.getElementById("uploadAttachmentBtn");
    const attachmentFile = document.getElementById("attachmentFile");

    console.log("⚙️ Upload elements found:", {
      uploadAttachmentBtn: !!uploadAttachmentBtn,
      attachmentFile: !!attachmentFile,
    });

    if (!uploadAttachmentBtn || !attachmentFile) {
      console.error("❌ Upload attachment elements not found in DOM");
      return;
    }

    // Upload attachment button click handler
    uploadAttachmentBtn.addEventListener("click", async function () {
      const files = attachmentFile.files;
      if (!files || files.length === 0) {
        showToast("Please select files to upload", "warning");
        return;
      }

      // Validate file sizes (10MB max)
      const maxSize = 10 * 1024 * 1024; // 10MB
      for (let file of files) {
        if (file.size > maxSize) {
          showToast(
            `File "${file.name}" is too large. Maximum size is 10MB.`,
            "error"
          );
          return;
        }
      }

      try {
        uploadAttachmentBtn.disabled = true;
        uploadAttachmentBtn.innerHTML =
          '<i class="fas fa-spinner fa-spin me-1"></i>Uploading...';

        // Show progress bar
        const uploadProgress = document.getElementById("uploadProgress");
        if (uploadProgress) {
          uploadProgress.classList.remove("d-none");
        }

        await uploadTaskAttachments(taskId, files);
        attachmentFile.value = ""; // Clear file input
        await loadTaskAttachments(taskId);
        showToast(`${files.length} file(s) uploaded successfully`, "success");
      } catch (error) {
        showToast("Failed to upload attachments", "error");
        console.error("Error uploading attachments:", error);
      } finally {
        uploadAttachmentBtn.disabled = false;
        uploadAttachmentBtn.innerHTML =
          '<i class="fas fa-upload me-1"></i>Upload';

        // Hide progress bar
        const uploadProgress = document.getElementById("uploadProgress");
        if (uploadProgress) {
          uploadProgress.classList.add("d-none");
        }
      }
    });

    // File input change handler to show selected files
    attachmentFile.addEventListener("change", function () {
      const files = this.files;
      if (files.length > 0) {
        const fileNames = Array.from(files)
          .map((f) => f.name)
          .join(", ");
        showToast(`Selected: ${fileNames}`, "info", 3000);
      }
    });
  }
  // Function to load task attachments
  async function loadTaskAttachments(taskId) {
    console.log("📎 Loading attachments for task:", taskId);
    const attachmentsList = document.getElementById("attachmentsList");
    const attachmentsCount = document.getElementById("attachmentsCount");
    const attachmentsLoading = document.getElementById("attachmentsLoading");
    const noAttachmentsMessage = document.getElementById(
      "noAttachmentsMessage"
    );

    console.log("📎 Elements found:", {
      attachmentsList: !!attachmentsList,
      attachmentsCount: !!attachmentsCount,
      attachmentsLoading: !!attachmentsLoading,
      noAttachmentsMessage: !!noAttachmentsMessage,
    });

    if (!attachmentsList || !attachmentsCount) {
      console.error("❌ Attachments elements not found in DOM");
      return;
    }
    try {
      // Show loading state
      if (attachmentsLoading) attachmentsLoading.classList.remove("d-none");
      if (noAttachmentsMessage) noAttachmentsMessage.classList.add("d-none");

      console.log(
        "📎 Fetching attachments from:",
        `/api/simple-tasks/${taskId}/attachments`
      );
      const response = await fetch(`/api/simple-tasks/${taskId}/attachments`, {
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      });

      console.log("📎 Response status:", response.status);
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          console.log("🔐 Authentication error, handling...");
          handleAuthenticationError();
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const attachments = await response.json();
      console.log("📎 Attachments loaded:", attachments);
      displayAttachments(attachments);
      attachmentsCount.textContent = attachments.length;
    } catch (error) {
      console.error("❌ Error loading attachments:", error);

      // Show error but still display the attachments section
      attachmentsList.innerHTML = `
        <div class="alert alert-warning">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Failed to load attachments. This might be because the attachments table doesn't exist yet.
          <br><small>Error: ${error.message}</small>
          <br><em>The upload functionality may not work until the database is set up.</em>
        </div>
      `;

      // Set count to 0 since we couldn't load
      attachmentsCount.textContent = "?";
    } finally {
      if (attachmentsLoading) attachmentsLoading.classList.add("d-none");
    }
  }

  // Function to display attachments
  function displayAttachments(attachments) {
    const attachmentsList = document.getElementById("attachmentsList");
    const noAttachmentsMessage = document.getElementById(
      "noAttachmentsMessage"
    );

    if (!attachmentsList) return;

    if (attachments.length === 0) {
      if (noAttachmentsMessage) noAttachmentsMessage.classList.remove("d-none");
      attachmentsList.innerHTML = `
        <div class="text-center text-muted py-3" id="noAttachmentsMessage">
          <i class="fas fa-file-slash me-2"></i>
          No attachments yet. Upload files to share with your team!
        </div>
      `;
      return;
    }

    if (noAttachmentsMessage) noAttachmentsMessage.classList.add("d-none");

    const attachmentsHtml = attachments
      .map((attachment) => {
        const uploadedDate = new Date(attachment.created_at).toLocaleString();
        const fileIcon = getFileIcon(attachment.filename);
        const fileSize = formatFileSize(attachment.file_size);

        return `
        <div class="attachment-item mb-2 p-3 border rounded">
          <div class="d-flex align-items-center justify-content-between">
            <div class="d-flex align-items-center">
              <div class="file-icon me-3">
                <i class="${fileIcon} fa-2x text-primary"></i>
              </div>
              <div>
                <div class="fw-bold">${attachment.filename}</div>
                <small class="text-muted">
                  ${fileSize} • Uploaded by ${
          attachment.user?.name || "Unknown User"
        } • ${uploadedDate}
                </small>
              </div>
            </div>
            <div class="attachment-actions">
              <a href="/api/simple-tasks/attachments/${attachment.id}/download" 
                 class="btn btn-sm btn-outline-primary me-2" 
                 title="Download">
                <i class="fas fa-download"></i>
              </a>
              <button type="button" 
                      class="btn btn-sm btn-outline-danger" 
                      onclick="deleteAttachment(${attachment.id}, '${
          attachment.filename
        }')"
                      title="Delete">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        </div>
      `;
      })
      .join("");

    attachmentsList.innerHTML = attachmentsHtml;
  }

  // Function to upload task attachments
  async function uploadTaskAttachments(taskId, files) {
    const formData = new FormData();

    for (let file of files) {
      formData.append("files", file);
    }

    const response = await fetch(`/api/simple-tasks/${taskId}/attachments`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: formData,
    });

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        handleAuthenticationError();
        return;
      }
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  }

  // Helper function to get file icon based on extension
  function getFileIcon(filename) {
    const extension = filename.split(".").pop().toLowerCase();

    const iconMap = {
      // Documents
      pdf: "fas fa-file-pdf",
      doc: "fas fa-file-word",
      docx: "fas fa-file-word",
      txt: "fas fa-file-alt",

      // Spreadsheets
      xls: "fas fa-file-excel",
      xlsx: "fas fa-file-excel",
      csv: "fas fa-file-csv",

      // Images
      jpg: "fas fa-file-image",
      jpeg: "fas fa-file-image",
      png: "fas fa-file-image",
      gif: "fas fa-file-image",
      bmp: "fas fa-file-image",
      svg: "fas fa-file-image",

      // Archives
      zip: "fas fa-file-archive",
      rar: "fas fa-file-archive",
      "7z": "fas fa-file-archive",

      // Code
      js: "fas fa-file-code",
      html: "fas fa-file-code",
      css: "fas fa-file-code",
      py: "fas fa-file-code",
      java: "fas fa-file-code",

      // Video
      mp4: "fas fa-file-video",
      avi: "fas fa-file-video",
      mov: "fas fa-file-video",

      // Audio
      mp3: "fas fa-file-audio",
      wav: "fas fa-file-audio",
    };

    return iconMap[extension] || "fas fa-file";
  }

  // Helper function to format file size
  function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";

    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  // Global function to delete attachment (called from HTML)
  window.deleteAttachment = async function (attachmentId, filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      const response = await fetch(
        `/api/simple-tasks/attachments/${attachmentId}`,
        {
          method: "DELETE",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
          credentials: "same-origin",
        }
      );

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          handleAuthenticationError();
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      showToast(`"${filename}" deleted successfully`, "success");

      // Reload attachments to update the list
      const taskDetailModal = document.getElementById("taskDetailModal");
      if (taskDetailModal) {
        // Get task ID from the modal or current context
        const taskId =
          taskDetailModal.getAttribute("data-task-id") ||
          document
            .querySelector(".task-card.active")
            ?.getAttribute("data-task-id");
        if (taskId) {
          loadTaskAttachments(taskId);
        }
      }
    } catch (error) {
      showToast("Failed to delete attachment", "error");
      console.error("Error deleting attachment:", error);
    }
  };
});
