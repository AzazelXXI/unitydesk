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
    } // Initialize assignment functionality
    setupTaskAssignmentHandlers(taskData); // Initialize attachments functionality
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
    const uploadAttachmentBtn = document.getElementById("uploadAttachmentBtn");
    const attachmentFile = document.getElementById("attachmentFile");

    if (!uploadAttachmentBtn || !attachmentFile) {
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
    const attachmentsList = document.getElementById("attachmentsList");
    const attachmentsCount = document.getElementById("attachmentsCount");
    const attachmentsLoading = document.getElementById("attachmentsLoading");
    const noAttachmentsMessage = document.getElementById(
      "noAttachmentsMessage"
    );

    if (!attachmentsList || !attachmentsCount) {
      return;
    }

    try {
      // Show loading state
      if (attachmentsLoading) attachmentsLoading.classList.remove("d-none");
      if (noAttachmentsMessage) noAttachmentsMessage.classList.add("d-none");

      const response = await fetch(`/api/simple-tasks/${taskId}/attachments`, {
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          handleAuthenticationError();
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const attachments = await response.json();
      displayAttachments(attachments);
      attachmentsCount.textContent = attachments.length;
    } catch (error) {
      console.error("Error loading attachments:", error);
      attachmentsList.innerHTML = `
        <div class="alert alert-warning">
          <i class="fas fa-exclamation-triangle me-2"></i>
          Failed to load attachments. Please try again.
        </div>
      `;
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

// Enhanced responsive behaviors (merged from task_list_responsive.js)
function initializeEnhancedResponsiveBehaviors() {
  // Check viewport size and device capabilities
  const isTouchDevice =
    "ontouchstart" in window || navigator.maxTouchPoints > 0;

  // Setup responsive table actions
  setupResponsiveTableActions();

  // Setup lazy loading for tasks if many exist
  setupLazyLoading();

  // Handle orientation changes on mobile devices
  window.addEventListener("orientationchange", handleOrientationChange);

  /**
   * Sets up alternative actions for table rows on small devices
   */
  function setupResponsiveTableActions() {
    // On very small screens, make the entire row clickable for details
    if (window.innerWidth < 576) {
      const taskRows = document.querySelectorAll("tbody tr");
      taskRows.forEach((row) => {
        // Skip rows that are already clickable
        if (row.querySelector('a[href*="/tasks/"]')) {
          row.style.cursor = "pointer";
          row.addEventListener("click", function (e) {
            // Don't trigger if they clicked a checkbox or button
            if (
              e.target.closest('input[type="checkbox"]') ||
              e.target.closest("button") ||
              e.target.closest("a")
            ) {
              return;
            }

            // Find the task ID
            const taskId = this.cells[1].textContent.trim(); // Assuming title is in the second cell
            // Redirect to task details
            window.location.href = `/tasks/${taskId}`;
          });
        }
      });
    }
  }

  /**
   * Sets up lazy loading for tasks if many exist
   */
  function setupLazyLoading() {
    // Implement if table has many rows
    const taskTable = document.querySelector(".table");
    if (taskTable && taskTable.rows.length > 20) {
      // Could implement virtual scrolling here
      console.log("Many tasks found, would benefit from virtual scrolling");
    }
  }

  /**
   * Handle device orientation changes
   */
  function handleOrientationChange() {
    // Force table to resize properly
    setTimeout(() => {
      const tableResponsive = document.querySelector(".table-responsive");
      if (tableResponsive) {
        tableResponsive.style.width = "99%";
        setTimeout(() => {
          tableResponsive.style.width = "100%";
        }, 50);
      }
    }, 100);
  }
}

// Initialize enhanced responsive behaviors
initializeEnhancedResponsiveBehaviors();
