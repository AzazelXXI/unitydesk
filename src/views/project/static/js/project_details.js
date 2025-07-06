// --- Member Role Update and Remove Functionality ---
document.addEventListener("DOMContentLoaded", function () {
  // Role change
  document.querySelectorAll(".save-role-btn").forEach(function (btn) {
    btn.addEventListener("click", async function (e) {
      e.preventDefault();
      const memberId = btn.getAttribute("data-member-id");
      const select = document.querySelector(
        `.member-role-select[data-member-id='${memberId}']`
      );
      const newRole = select.value;
      const projectId = getProjectIdFromUrl();
      btn.disabled = true;
      try {
        const response = await fetch(`/projects/${projectId}/members/${memberId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role: newRole }),
          credentials: "include",
        });
        const result = await response.json();
        if (result.success) {
          alert("Role updated successfully!");
          window.location.reload();
        } else {
          alert("Failed to update role: " + (result.message || "Unknown error"));
        }
      } catch (err) {
        alert("Error updating role. Please try again.");
      }
      btn.disabled = false;
    });
  });

  // Remove member
  document.querySelectorAll(".remove-member-btn").forEach(function (btn) {
    btn.addEventListener("click", async function (e) {
      e.preventDefault();
      if (!confirm("Are you sure you want to remove this member from the project?")) return;
      const memberId = btn.getAttribute("data-member-id");
      const projectId = getProjectIdFromUrl();
      btn.disabled = true;
      try {
        const response = await fetch(`/projects/${projectId}/members/${memberId}`, {
          method: "DELETE",
          credentials: "include",
        });
        const result = await response.json();
        if (result.success) {
          alert("Member removed successfully!");
          window.location.reload();
        } else {
          alert("Failed to remove member: " + (result.message || "Unknown error"));
        }
      } catch (err) {
        alert("Error removing member. Please try again.");
      }
      btn.disabled = false;
    });
  });
});
/**
 * Project Details Page JavaScript
 * Handles task management, modals, filtering, and project interactions
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize page functionality
  initializeProjectTabs();
  initializeTaskModal();
  initializeAddTaskForm();
  initializeAddMemberForm();
  initializeTaskFiltering();
  initializeProjectActions();
});

/**
 * Initialize Bootstrap tabs and handle "View All" button
 */
function initializeProjectTabs() {
  const viewAllTasksBtn = document.querySelector('a[data-bs-target="#tasks"]');
  if (viewAllTasksBtn) {
    viewAllTasksBtn.addEventListener("click", function (e) {
      e.preventDefault();

      // Get the tab button (not the pane)
      const tabButton = document.querySelector("#tasks-tab");

      if (tabButton) {
        // Create Bootstrap tab instance and show it
        const tab = new bootstrap.Tab(tabButton);
        tab.show();
      }
    });
  }
}

/**
 * Initialize task details modal functionality
 */
function initializeTaskModal() {
  const taskDetailsModal = document.getElementById("taskDetailsModal");
  const taskDetailsContent = document.getElementById("taskDetailsContent");

  // Handle task card clicks
  document.querySelectorAll(".clickable-task").forEach((card) => {
    card.addEventListener("click", function () {
      const taskId = this.getAttribute("data-task-id");
      loadTaskDetails(taskId);
    });
  });

  /**
   * Load task details from API and display in modal
   */
  async function loadTaskDetails(taskId) {
    try {
      taskDetailsContent.innerHTML = `
        <div class="text-center py-3">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
      `;

      const response = await fetch(`/api/tasks/${taskId}`, {
        credentials: "include",
      });

      if (response.ok) {
        const task = await response.json();
        displayTaskDetails(task);
      } else {
        taskDetailsContent.innerHTML = `
          <div class="alert alert-danger">
            Failed to load task details. Please try again.
          </div>
        `;
      }
    } catch (error) {
      console.error("Error loading task details:", error);
      taskDetailsContent.innerHTML = `
        <div class="alert alert-danger">
          An error occurred while loading task details.
        </div>
      `;
    }
  }

  /**
   * Display task details in the modal with organized containers
   */
  function displayTaskDetails(task) {
    const statusClass = getStatusClass(task.status);
    const priorityClass = getPriorityClass(task.priority);

    // Set the clone form action for this task
    setCloneTaskFormAction(task.id);

    taskDetailsContent.innerHTML = `
      <div class="task-details-container">
        <!-- Task Header Container -->
        <div class="task-section-container bg-light rounded p-3 mb-4">
          <div class="task-header">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <h3 class="task-title mb-0">${task.name}</h3>
              <div class="task-badges">
                <span class="badge ${statusClass} me-2">${
      task.status ? task.status.replace("_", " ").toUpperCase() : "NOT STARTED"
    }</span>
                <span class="badge ${priorityClass}">${
      task.priority || "MEDIUM"
    }</span>
              </div>
            </div>
            <div class="task-meta text-muted">
              <small>Created: ${new Date(task.created_at).toLocaleDateString(
                "en-US",
                { year: "numeric", month: "short", day: "numeric" }
              )}</small>
            </div>
          </div>
        </div>

        <!-- Description Container -->
        <div class="task-section-container bg-white border rounded p-3 mb-4">
          <div class="task-section">
            <div class="section-header d-flex align-items-center mb-3">
              <i class="bi bi-file-text me-2 text-primary"></i>
              <h5 class="section-title mb-0">Description</h5>
            </div>
            <div class="section-content">
              <p class="mb-0">${
                task.description || "No description provided"
              }</p>
            </div>
          </div>
        </div>

        <!-- Task Details Grid Container -->
        <div class="task-section-container bg-white border rounded p-3 mb-4">
          <div class="row">
            <!-- Due Date -->
            <div class="col-md-6">
              <div class="task-section">
                <div class="section-header d-flex align-items-center mb-3">
                  <i class="bi bi-calendar me-2 text-primary"></i>
                  <h5 class="section-title mb-0">Due Date</h5>
                </div>
                <div class="section-content">
                  <p class="mb-0">${
                    task.due_date
                      ? new Date(task.due_date).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })
                      : "No due date set"
                  }</p>
                </div>
              </div>
            </div>

            <!-- Assigned To -->
            <div class="col-md-6">
              <div class="task-section">
                <div class="section-header d-flex align-items-center mb-3">
                  <i class="bi bi-person me-2 text-primary"></i>
                  <h5 class="section-title mb-0">Assigned To</h5>
                  <button class="btn btn-primary btn-sm ms-auto" id="changeAssigneesBtn" style="display:none;">Assign</button>
                </div>
                <div class="section-content">
                  ${
                    task.assignee_names && task.assignee_names.length > 0
                      ? task.assignee_names
                          .map(
                            (name, index) => `
                          <div class="d-flex align-items-center mb-2">
                            <div class="user-avatar me-2">
                              ${name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")
                                .toUpperCase()}
                            </div>
                            <span>${name}</span>
                          </div>
                        `
                          )
                          .join("")
                      : `
                        <div class="d-flex align-items-center">
                          <div class="user-avatar me-2">UN</div>
                          <span>Unassigned</span>
                        </div>
                      `
                  }
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Project Container -->
        <div class="task-section-container bg-white border rounded p-3 mb-4">
          <div class="task-section">
            <div class="section-header d-flex align-items-center mb-3">
              <i class="bi bi-folder me-2 text-primary"></i>
              <h5 class="section-title mb-0">Project</h5>
            </div>
            <div class="section-content">
              <a href="/projects/${getProjectIdFromUrl()}" class="text-decoration-none">${getProjectNameFromPage()}</a>
            </div>
          </div>
        </div>

        <!-- Attachments Container -->
        <div class="task-section-container bg-white border rounded p-3 mb-4">
          <div class="task-section">
            <div class="section-header d-flex align-items-center mb-3">
              <i class="bi bi-paperclip me-2 text-primary"></i>
              <h5 class="section-title mb-0">Attachments</h5>
              <span class="badge bg-secondary ms-2">0</span>
            </div>
            <div class="section-content">
              <div class="attachment-area text-center py-4 bg-light border border-dashed rounded">
                <button class="btn btn-sm btn-outline-secondary me-2">Browse...</button>
                <span class="text-muted">No files selected.</span>
                <button class="btn btn-sm btn-primary ms-2">Upload</button>
              </div>
              <small class="text-muted d-block mt-2">Supported: PDF, DOC, XLS, TXT, Images, ZIP (Max 10MB each)</small>
              <div class="text-center mt-3">
                <p class="text-muted mb-0">No attachments yet. Upload files to share with your team!</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Comments Container -->
        <div class="task-section-container bg-white border rounded p-3">
          <div class="task-section">
            <div class="section-header d-flex align-items-center mb-3">
              <i class="bi bi-chat-dots me-2 text-primary"></i>
              <h5 class="section-title mb-0">Comments</h5>
              <span class="badge bg-secondary ms-2">0</span>
            </div>
            <div class="section-content">
              <div class="comments-area">
                <div class="comment-form mb-3">
                  <textarea class="form-control" rows="3" placeholder="Add a comment..."></textarea>
                  <div class="d-flex justify-content-end mt-2">
                    <button class="btn btn-primary btn-sm">
                      <i class="bi bi-send me-1"></i>Post Comment
                    </button>
                  </div>
                </div>
                <div class="text-center text-muted py-3">
                  <i class="bi bi-chat-dots" style="font-size: 2rem;"></i>
                  <p class="mb-0 mt-2">No comments yet. Be the first to add one!</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    // Show Assign button only for project owner (like Delete/Clone Task)
    setTimeout(function() {
      const assignBtn = document.getElementById('changeAssigneesBtn');
      if (assignBtn) {
        // Debug output
        console.log('[DEBUG] Assign button logic:', {
          projectOwnerId: window.projectOwnerId,
          currentUserId: window.currentUserId,
          task_owner_id: task.owner_id,
          creator_id: task.creator_id
        });
        // Show if current user is project owner (from API) or task creator
        if (
          (task.owner_id && window.currentUserId && task.owner_id == window.currentUserId) ||
          (task.creator_id && window.currentUserId && task.creator_id == window.currentUserId)
        ) {
          assignBtn.style.display = '';
        } else {
          assignBtn.style.display = 'none';
        }
      }
    }, 0);
  }

  // Make loadTaskDetails available globally for potential external calls
  window.loadTaskDetails = loadTaskDetails;
}

/**
 * Initialize Add Task form functionality
 */
function initializeAddTaskForm() {
  const addTaskForm = document.getElementById("addTaskForm");
  if (addTaskForm) {
    // Initialize dynamic assignee functionality
    initializeDynamicAssignees();

    addTaskForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData();
      const projectId = getProjectIdFromUrl();

      // Get all form fields
      formData.append("taskName", document.getElementById("taskName").value);
      formData.append(
        "taskDescription",
        document.getElementById("taskDescription").value
      );
      formData.append(
        "taskPriority",
        document.getElementById("taskPriority").value
      );
      formData.append(
        "taskStatus",
        document.getElementById("taskStatus").value
      );
      formData.append(
        "taskStartDate",
        document.getElementById("taskStartDate").value
      );
      formData.append(
        "taskDueDate",
        document.getElementById("taskDueDate").value
      );
      formData.append(
        "taskEstimatedHours",
        document.getElementById("taskEstimatedHours").value
      );

      // Collect all selected assignees from dynamic dropdowns
      const assigneeSelects = document.querySelectorAll(".assignee-select");
      assigneeSelects.forEach((select) => {
        if (select.value && select.value !== "") {
          formData.append("taskAssignees", select.value);
        }
      });

      try {
        const response = await fetch(`/projects/${projectId}/tasks`, {
          method: "POST",
          body: formData,
          credentials: "include",
        });

        const result = await response.json();

        if (result.success) {
          // Close the modal
          const modal = bootstrap.Modal.getInstance(
            document.getElementById("addTaskModal")
          );
          modal.hide();

          // Reset the form
          addTaskForm.reset();
          resetDynamicAssignees();

          // Show success message
          alert("Task created successfully!");

          // Reload the page to show the new task
          window.location.reload();
        } else {
          alert("Error creating task: " + (result.message || "Unknown error"));
        }
      } catch (error) {
        console.error("Error creating task:", error);
        alert("Error creating task. Please try again.");
      }
    });
  }
}

/**
 * Initialize dynamic assignee functionality
 */
function initializeDynamicAssignees() {
  const assigneeContainer = document.getElementById("assigneeContainer");
  if (!assigneeContainer) return;

  // Add event listeners for existing add buttons
  addAssigneeEventListeners();
}

/**
 * Add event listeners to assignee add/remove buttons
 */
function addAssigneeEventListeners() {
  // Add event listeners to all add buttons
  document.querySelectorAll(".add-assignee-btn").forEach((btn) => {
    btn.addEventListener("click", addAssigneeRow);
  });

  // Add event listeners to all remove buttons
  document.querySelectorAll(".remove-assignee-btn").forEach((btn) => {
    btn.addEventListener("click", removeAssigneeRow);
  });

  // Add event listeners to select changes to hide/show used options
  document.querySelectorAll(".assignee-select").forEach((select) => {
    select.addEventListener("change", updateAvailableOptions);
  });
}

/**
 * Add a new assignee row
 */
function addAssigneeRow() {
  const assigneeContainer = document.getElementById("assigneeContainer");
  const existingRows = assigneeContainer.querySelectorAll(".assignee-row");

  // Get the template from the first row
  const firstRow = existingRows[0];
  const newRow = firstRow.cloneNode(true);

  // Reset the select value
  const newSelect = newRow.querySelector(".assignee-select");
  newSelect.value = "";

  // Replace add button with remove button (except for the first row)
  const addBtn = newRow.querySelector(".add-assignee-btn");
  if (existingRows.length > 0) {
    addBtn.className = "btn btn-outline-danger btn-sm remove-assignee-btn";
    addBtn.innerHTML = '<i class="bi bi-dash"></i>';
    addBtn.title = "Remove this assignee";
  }

  // Add the new row
  assigneeContainer.appendChild(newRow);

  // Re-initialize event listeners
  addAssigneeEventListeners();

  // Update available options
  updateAvailableOptions();
}

/**
 * Remove an assignee row
 */
function removeAssigneeRow(event) {
  const row = event.target.closest(".assignee-row");
  const assigneeContainer = document.getElementById("assigneeContainer");

  // Don't remove if it's the only row
  if (assigneeContainer.querySelectorAll(".assignee-row").length > 1) {
    row.remove();
    updateAvailableOptions();
  }
}

/**
 * Update available options in all dropdowns to prevent duplicates
 */
function updateAvailableOptions() {
  const allSelects = document.querySelectorAll(".assignee-select");
  const selectedValues = Array.from(allSelects)
    .map((select) => select.value)
    .filter((value) => value !== "");

  allSelects.forEach((select) => {
    const currentValue = select.value;
    const options = select.querySelectorAll("option");

    options.forEach((option) => {
      if (option.value === "") return; // Skip the "Select a user..." option

      // Hide option if it's selected in another dropdown
      if (
        selectedValues.includes(option.value) &&
        option.value !== currentValue
      ) {
        option.style.display = "none";
      } else {
        option.style.display = "";
      }
    });
  });
}

/**
 * Reset dynamic assignees to initial state
 */
function resetDynamicAssignees() {
  const assigneeContainer = document.getElementById("assigneeContainer");
  if (!assigneeContainer) return;

  // Remove all rows except the first one
  const rows = assigneeContainer.querySelectorAll(".assignee-row");
  for (let i = 1; i < rows.length; i++) {
    rows[i].remove();
  }

  // Reset the first row
  const firstRow = assigneeContainer.querySelector(".assignee-row");
  if (firstRow) {
    const select = firstRow.querySelector(".assignee-select");
    select.value = "";

    // Make sure the first row has an add button
    const btn = firstRow.querySelector("button");
    btn.className = "btn btn-outline-success btn-sm add-assignee-btn";
    btn.innerHTML = '<i class="bi bi-plus"></i>';
    btn.title = "Add another assignee";
  }

  // Update available options
  updateAvailableOptions();
}

/**
 * Initialize Add Member form functionality
 */
function initializeAddMemberForm() {
  const addMemberForm = document.getElementById("addMemberForm");
  if (addMemberForm) {
    addMemberForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(addMemberForm);
      const projectId = getProjectIdFromUrl();

      // Create the data object
      const memberData = {
        user_id: formData.get("memberUser"),
        role: formData.get("memberRole"),
      };

      try {
        const response = await fetch(`/projects/${projectId}/members`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(memberData),
          credentials: "include",
        });

        const result = await response.json();

        if (result.success) {
          // Close the modal
          const modal = bootstrap.Modal.getInstance(
            document.getElementById("addMemberModal")
          );
          modal.hide();

          // Reset the form
          addMemberForm.reset();

          // Show success message
          alert("Member added successfully!");

          // Reload the page to show the new member
          window.location.reload();
        } else {
          alert("Error adding member: " + (result.message || "Unknown error"));
        }
      } catch (error) {
        console.error("Error adding member:", error);
        alert("Error adding member. Please try again.");
      }
    });
  }
}

/**
 * Initialize task filtering functionality
 */
function initializeTaskFiltering() {
  // Auto-submit task filters on select changes for better UX
  const taskSelects = document.querySelectorAll(
    "#task_status, #task_priority, #task_assignee, #task_sort_by, #task_sort_order"
  );
  taskSelects.forEach((select) => {
    select.addEventListener("change", function () {
      document.getElementById("taskFilterForm").submit();
    });
  });

  // Add search input event listener with debounce
  const taskSearchInput = document.getElementById("task_search");
  if (taskSearchInput) {
    let taskSearchTimeout;
    taskSearchInput.addEventListener("input", function () {
      clearTimeout(taskSearchTimeout);
      taskSearchTimeout = setTimeout(() => {
        document.getElementById("taskFilterForm").submit();
      }, 500); // 500ms debounce
    });
  }
}

/**
 * Initialize project actions (delete project, etc.)
 */
function initializeProjectActions() {
  const deleteProjectBtn = document.getElementById("deleteProjectBtn");
  if (deleteProjectBtn) {
    deleteProjectBtn.addEventListener("click", async function (e) {
      e.preventDefault();

      const projectId = getProjectIdFromUrl();
      const projectName = getProjectNameFromPage();

      // Confirm deletion
      const confirmMessage = `Are you sure you want to delete the project "${projectName}"? This action cannot be undone.`;

      if (!confirm(confirmMessage)) {
        return;
      }

      try {
        console.log(`Deleting project ${projectId}...`);

        const response = await fetch(`/api/projects/${projectId}`, {
          method: "DELETE",
          credentials: "include",
        });

        if (response.ok) {
          console.log(`✅ Successfully deleted project ${projectId}`);
          alert(`Project "${projectName}" has been deleted successfully!`);

          // Redirect to projects list
          window.location.href = "/projects";
        } else {
          console.error(
            `❌ Failed to delete project ${projectId}:`,
            response.status
          );
          alert("Failed to delete the project. Please try again.");
        }
      } catch (error) {
        console.error(`❌ Error deleting project ${projectId}:`, error);
        alert(
          "An error occurred while deleting the project. Please try again."
        );
      }
    });
  }
}

/**
 * Utility Functions
 */

function getStatusClass(status) {
  switch (status) {
    case "COMPLETED":
      return "bg-success";
    case "IN_PROGRESS":
      return "bg-primary";
    case "BLOCKED":
      return "bg-warning text-dark";
    default:
      return "bg-secondary";
  }
}

function getPriorityClass(priority) {
  switch (priority) {
    case "HIGH":
    case "URGENT":
      return "bg-danger";
    case "MEDIUM":
      return "bg-warning text-dark";
    case "LOW":
      return "bg-info";
    default:
      return "bg-warning text-dark";
  }
}

function getProjectIdFromUrl() {
  // Extract project ID from the current URL
  const pathParts = window.location.pathname.split("/");
  const projectIndex = pathParts.indexOf("projects");
  return projectIndex !== -1 && pathParts[projectIndex + 1]
    ? pathParts[projectIndex + 1]
    : null;
}

function getProjectNameFromPage() {
  // Get project name from the page title or header
  const projectHeader = document.querySelector(".project-header h1");
  return projectHeader ? projectHeader.textContent.trim() : "Project";
}

/**
 * Global Functions - Available for external calls
 */

// Function to show a specific tab
window.showTab = function (tabName) {
  const tabButton = document.querySelector(`#${tabName}-tab`);
  if (tabButton) {
    const tab = new bootstrap.Tab(tabButton);
    tab.show();
  }
};

// Task filtering functionality
window.clearTaskFilters = function () {
  // Clear all task filter values
  document.getElementById("task_status").value = "all";
  document.getElementById("task_priority").value = "all";
  document.getElementById("task_assignee").value = "all";
  document.getElementById("task_sort_by").value = "created_at";
  document.getElementById("task_sort_order").value = "desc";
  document.getElementById("task_search").value = "";

  // Submit the form to apply cleared filters
  document.getElementById("taskFilterForm").submit();
};

// Task action functions
window.markTaskComplete = async function (taskId) {
  try {
    const response = await fetch(`/api/tasks/${taskId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({ status: "COMPLETED" }),
    });

    if (response.ok) {
      // Reload task details and refresh the page
      await window.loadTaskDetails(taskId);
      location.reload();
    } else {
      alert("Failed to update task status");
    }
  } catch (error) {
    console.error("Error updating task:", error);
    alert("An error occurred while updating the task");
  }
};

window.editTask = function (taskId) {
  // Close the details modal and open edit modal
  const detailsModal = bootstrap.Modal.getInstance(
    document.getElementById("taskDetailsModal")
  );
  detailsModal.hide();

  // You can implement task editing here
  alert("Task editing feature coming soon!");
};

window.deleteTask = async function (taskId) {
  if (confirm("Are you sure you want to delete this task?")) {
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.ok) {
        // Close modal and refresh page
        const detailsModal = bootstrap.Modal.getInstance(
          document.getElementById("taskDetailsModal")
        );
        detailsModal.hide();
        location.reload();
      } else {
        alert("Failed to delete task");
      }
    } catch (error) {
      console.error("Error deleting task:", error);
      alert("An error occurred while deleting the task");
    }
  }
};
