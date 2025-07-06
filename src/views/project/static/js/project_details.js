// Declare taskDetailsModal globally at the top of the script
let taskDetailsModal = null;

// --- Member Role Update and Remove Functionality ---
document.addEventListener("DOMContentLoaded", function () {
  // Initialize taskDetailsModal once when the DOM is fully loaded
  taskDetailsModal = document.getElementById("taskDetailsModal");

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
    // Map backend string to enum for color and dropdown selection
    const statusMap = {
      NOT_STARTED: 'Not Started',
      IN_PROGRESS: 'In Progress',
      BLOCKED: 'Blocked',
      COMPLETED: 'Completed',
      CANCELLED: 'Cancelled'
    };
    const priorityMap = {
      LOW: 'Low',
      MEDIUM: 'Medium',
      HIGH: 'High',
      URGENT: 'Urgent'
    };
    // Reverse map for backend string to enum key
    function getStatusEnum(str) {
      return Object.keys(statusMap).find(key => statusMap[key] === str) || str;
    }
    function getPriorityEnum(str) {
      return Object.keys(priorityMap).find(key => priorityMap[key] === str) || str;
    }
    const statusEnum = getStatusEnum(task.status);
    const priorityEnum = getPriorityEnum(task.priority);
    const statusClass = getStatusClass(statusEnum);
    const priorityClass = getPriorityClass(priorityEnum);

    // Set the clone form action for this task
    setCloneTaskFormAction(task.id);

    // Store users for multi-select (assume window.allUsers is set server-side)
    const allUsers = window.allUsers || [];
    // Helper to render assignee avatars
    function renderAssignees(names) {
      if (!names || names.length === 0) {
        return `<div class="d-flex align-items-center"><div class="user-avatar me-2">UN</div><span>Unassigned</span></div>`;
      }
      return names.map(function(name) {
        return `<div class="d-flex align-items-center mb-2"><div class="user-avatar me-2">${name.split(" ").map(function(n){return n[0];}).join("").toUpperCase()}</div><span>${name}</span></div>`;
      }).join("");
    }

    // Determine if the current user is the creator
    // window.currentUserId should be set server-side in the template
    const isCreator = window.currentUserId && task.creator_id && window.currentUserId === task.creator_id;
    // Clear previous content to avoid ReferenceError
    taskDetailsContent.innerHTML = "";
    // Now set the modal content
    taskDetailsContent.innerHTML = `
      <div class="task-details-container">
        <!-- Task Header Container -->
        <div class="task-section-container bg-light rounded p-3 mb-4">
          <div class="task-header">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div class="d-flex align-items-center">
                <h3 class="task-title mb-0">${task.name}</h3>
              </div>
              <div class="d-flex flex-column align-items-end ms-3">
                <span class="badge ${statusClass} mb-1" id="taskStatusBadge">
                  ${statusMap[statusEnum] || 'Not Started'}
                </span>
                <span class="badge ${priorityClass}" id="taskPriorityBadge">
                  ${priorityMap[priorityEnum] || 'Medium'}
                </span>
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

        <!-- Status & Priority Section -->
        <div class="task-section-container bg-white border rounded p-3 mb-4">
          <div class="task-section">
            <div class="section-header d-flex align-items-center justify-content-between mb-3">
              <div class="d-flex align-items-center">
                <i class="bi bi-flag me-2 text-primary"></i>
                <h5 class="section-title mb-0">Status & Priority</h5>
              </div>
              <button class="btn btn-primary btn-sm" id="applyStatusChangeBtn" type="button">Change</button>
            </div>
            <div class="section-content">
              <div class="mb-2 d-flex align-items-center">
                <label class="form-label fw-bold mb-0 me-2">Status</label>
                <select class="form-select form-select-sm d-inline-block w-auto align-middle" id="taskStatusDropdown">
                  <option value="NOT_STARTED" ${statusEnum === 'NOT_STARTED' ? 'selected' : ''}>Not Started</option>
                  <option value="IN_PROGRESS" ${statusEnum === 'IN_PROGRESS' ? 'selected' : ''}>In Progress</option>
                  <option value="BLOCKED" ${statusEnum === 'BLOCKED' ? 'selected' : ''}>Blocked</option>
                  <option value="COMPLETED" ${statusEnum === 'COMPLETED' ? 'selected' : ''}>Completed</option>
                </select>
              </div>
              <div class="mb-2">
                <label class="form-label fw-bold">Priority</label>
                <select class="form-select form-select-sm w-auto d-inline-block" id="taskPriorityDropdown">
                  <option value="LOW" ${priorityEnum === 'LOW' ? 'selected' : ''}>Low</option>
                  <option value="MEDIUM" ${priorityEnum === 'MEDIUM' ? 'selected' : ''}>Medium</option>
                  <option value="HIGH" ${priorityEnum === 'HIGH' ? 'selected' : ''}>High</option>
                  <option value="URGENT" ${priorityEnum === 'URGENT' ? 'selected' : ''}>Urgent</option>
                </select>
              </div>
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
              <div class="task-section" id="assigneeSection">
                <div class="section-header d-flex align-items-center mb-3">
                  <i class="bi bi-person me-2 text-primary"></i>
                  <h5 class="section-title mb-0">Assigned To</h5>
                  ${isCreator ? `<button class="btn btn-primary btn-sm ms-auto" id="changeAssigneesBtn">Assign</button>` : ""}
                </div>
                <div class="section-content" id="assigneeListContent">
                  ${renderAssignees(task.assignee_names)}
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
    // End of modal content

    // Attach event handler for Change button (multi-select assignees) after modal HTML is set
    // This ensures the button is interactive and triggers the dropdown logic handled by task_details_modal.js
    setTimeout(function() {
      const changeBtn = document.getElementById("changeAssigneesBtn");
      if (changeBtn) {
        changeBtn.onclick = null;
        changeBtn.addEventListener("click", async function(e) {
          e.preventDefault();
          console.log('[DEBUG] Assign button clicked');
          const assigneeListContent = document.getElementById("assigneeListContent");
          // Fetch assignable members from backend API
          let members = [];
          try {
            const projectId = getProjectIdFromUrl();
            const resp = await fetch(`/api/projects/${projectId}/tasks/${task.id}/unassigned-members`, { credentials: "include" });
            if (resp.ok) {
              const data = await resp.json();
              console.log('[DEBUG] Assignable members from API:', data);
              members = Array.isArray(data.unassigned_members) ? data.unassigned_members : [];
            } else {
              console.warn('[DEBUG] Failed to fetch assignable members, status:', resp.status);
            }
          } catch (err) {
            console.error('[DEBUG] Error fetching assignable members:', err);
          }
          let dropdownHtml = `<div class='mb-2'><select id='taskAssigneeDropdown' class='form-select form-select-sm'>`;
          let hasAssignable = false;
          if (!Array.isArray(members) || members.length === 0) {
            dropdownHtml += `<option value=''>No members available</option>`;
          } else {
            dropdownHtml += `<option value=''>Select a member...</option>`;
            for (const member of members) {
              dropdownHtml += `<option value='${member.id}'>${member.name}</option>`;
              hasAssignable = true;
            }
            if (!hasAssignable) {
              dropdownHtml = `<div class='mb-2'><select id='taskAssigneeDropdown' class='form-select form-select-sm'><option value=''>No members available</option></select></div>`;
            }
          }
          dropdownHtml += `</select></div>`;
          dropdownHtml += `<button type='button' class='btn btn-primary btn-sm' id='assignMemberBtn'>Apply</button> `;
          dropdownHtml += `<button type='button' class='btn btn-secondary btn-sm ms-2' id='cancelAssigneeEdit'>Cancel</button>`;
          assigneeListContent.innerHTML = dropdownHtml;

          document.getElementById("cancelAssigneeEdit").onclick = function() {
            assigneeListContent.innerHTML = renderAssignees(task.assignee_names);
          };
          document.getElementById("assignMemberBtn").onclick = async function() {
            const select = document.getElementById("taskAssigneeDropdown");
            const selectedId = select.value;
            if (!selectedId) {
              alert("Please select a member to assign.");
              return;
            }
            this.disabled = true;
            try {
              // Get current assignees and add the new one to the list
              const currentAssignees = task.assignee_ids || [];
              const newAssignees = [...currentAssignees, parseInt(selectedId)];
              console.log('[DEBUG] PATCH /api/tasks/' + task.id, { assignees: newAssignees });
              const patchResp = await fetch(`/api/tasks/${task.id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ assignees: newAssignees })
              });
              if (!patchResp.ok) throw new Error("Failed to assign member");
              // Instead of just updating the assignee section, reload the full task details to ensure all assignees are shown
              await loadTaskDetails(task.id);
            } catch (err) {
              alert("Failed to assign member.");
            } finally {
              this.disabled = false;
            }
          };
        });
      }
    }, 0);

    // Store the current task ID on the modal for event handlers
    if (taskDetailsModal) {
      taskDetailsModal.setAttribute('data-task-id', task.id);
      const modalInstance = bootstrap.Modal.getOrCreateInstance(taskDetailsModal);
      modalInstance.show();
    }
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

// Ensure taskDetailsModal is declared only once at the top of the script
// let taskDetailsModal = document.getElementById("taskDetailsModal");

if (taskDetailsModal) {
  taskDetailsModal.addEventListener("click", async function (event) {
    if (event.target && event.target.id === "applyStatusChangeBtn") {
      console.log('[DEBUG] Change button clicked');
      const statusDropdown = document.getElementById("taskStatusDropdown");
      const priorityDropdown = document.getElementById("taskPriorityDropdown");
      const applyBtn = event.target;
      // Get the current task ID from the modal's data attribute
      const taskId = taskDetailsModal.getAttribute('data-task-id');
      if (statusDropdown && priorityDropdown && applyBtn && taskId) {
        const newStatus = statusDropdown.value;
        const newPriority = priorityDropdown.value;
        statusDropdown.disabled = true;
        priorityDropdown.disabled = true;
        applyBtn.disabled = true;
        applyBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>Saving...';
        try {
          console.log('[DEBUG] Attempting PATCH /api/tasks/' + taskId, { status: newStatus, priority: newPriority });
          const response = await fetch(`/api/tasks/` + taskId, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify({ status: newStatus, priority: newPriority })
          });
          console.log('[DEBUG] PATCH response status:', response.status);
          if (!response.ok) {
            alert("Failed to update status/priority");
            throw new Error("Failed to update status/priority");
          }
          const updatedTask = await response.json();
          console.log('[DEBUG] PATCH response data:', updatedTask);
          const statusBadge = document.getElementById("taskStatusBadge");
          const priorityBadge = document.getElementById("taskPriorityBadge");
          if (statusBadge) {
            statusBadge.className = "badge " + getStatusClass(updatedTask.status) + " mb-1";
            statusBadge.textContent = updatedTask.status.replace(/_/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
          }
          if (priorityBadge) {
            priorityBadge.className = "badge " + getPriorityClass(updatedTask.priority);
            priorityBadge.textContent = updatedTask.priority ? updatedTask.priority.charAt(0) + updatedTask.priority.slice(1).toLowerCase() : 'Medium';
          }
          alert("Status & Priority updated!");
        } catch (err) {
          console.error('[DEBUG] Error in PATCH:', err);
          alert("Error updating status/priority");
        } finally {
          statusDropdown.disabled = false;
          priorityDropdown.disabled = false;
          applyBtn.disabled = false;
          applyBtn.innerHTML = 'Change';
        }
      } else {
        console.error('[DEBUG] Could not find status/priority dropdowns or change button or taskId');
      }
    }
  });
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
}
