// --- Utility Functions ---
/**
 * Extract project ID from the current URL
 * URL format: /projects/{project_id}
 */
function getProjectIdFromUrl() {
  const path = window.location.pathname;
  const match = path.match(/\/projects\/(\d+)/);
  return match ? match[1] : null;
}

/**
 * Get CSS class for task status
 */
function getStatusClass(status) {
  switch (status?.toLowerCase()) {
    case 'pending':
      return 'bg-secondary text-light';
    case 'in_progress':
      return 'bg-primary text-light';
    case 'completed':
      return 'bg-success text-light';
    case 'cancelled':
      return 'bg-danger text-light';
    default:
      return 'bg-secondary text-light';
  }
}

/**
 * Get CSS class for task priority
 */
function getPriorityClass(priority) {
  switch (priority?.toLowerCase()) {
    case 'low':
      return 'bg-success text-light';
    case 'medium':
      return 'bg-warning text-dark';
    case 'high':
      return 'bg-danger text-light';
    default:
      return 'bg-secondary text-light';
  }
}

/**
 * Get project name from the page title or heading
 */
function getProjectNameFromPage() {
  // Try to get from page title first
  const titleElement = document.querySelector('h1, .project-title, [data-project-name]');
  if (titleElement) {
    return titleElement.textContent.trim();
  }
  
  // Fallback to document title
  const title = document.title;
  const match = title.match(/Project: (.+)/);
  return match ? match[1] : 'Project';
}

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
  initializeFilesTab();
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
    // setCloneTaskFormAction(task.id);

    taskDetailsContent.innerHTML = `
      <div class="task-details-container">
        <!-- Task Header Container -->
        <div class="task-section-container bg-light rounded p-3 mb-4">
          <div class="task-header">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <h3 class="task-title mb-0">${task.name}</h3>
              <div class="task-badges">
                <span class="badge ${statusClass} me-2">${task.status || "Not Started"}</span>
                <span class="badge ${priorityClass}">${task.priority || "Medium"}</span>
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
              <button class="btn btn-primary btn-sm" id="changeStatusPriorityBtn" type="button">Change</button>
            </div>
            <div class="section-content">
              <div class="row">
                <div class="col-md-6">
                  <label class="form-label fw-bold">Status</label>
                  <select class="form-select form-select-sm" id="taskStatusDropdown">
                    <option value="NOT_STARTED" ${task.status === 'Not Started' ? 'selected' : ''}>Not Started</option>
                    <option value="IN_PROGRESS" ${task.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                    <option value="BLOCKED" ${task.status === 'Blocked' ? 'selected' : ''}>Blocked</option>
                    <option value="COMPLETED" ${task.status === 'Completed' ? 'selected' : ''}>Completed</option>
                    <option value="CANCELLED" ${task.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label fw-bold">Priority</label>
                  <select class="form-select form-select-sm" id="taskPriorityDropdown">
                    <option value="LOW" ${task.priority === 'Low' ? 'selected' : ''}>Low</option>
                    <option value="MEDIUM" ${task.priority === 'Medium' ? 'selected' : ''}>Medium</option>
                    <option value="HIGH" ${task.priority === 'High' ? 'selected' : ''}>High</option>
                    <option value="URGENT" ${task.priority === 'Urgent' ? 'selected' : ''}>Urgent</option>
                  </select>
                </div>
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
              <div class="task-section">
                <div class="section-header d-flex align-items-center mb-3">
                  <i class="bi bi-person me-2 text-primary"></i>
                  <h5 class="section-title mb-0">Assigned To</h5>
                  <button class="btn btn-primary btn-sm ms-auto" id="changeAssigneesBtn">Assign</button>
                </div>
                <div class="section-content" id="assignedMembersContent">
                  ${
                    task.assignee_names && task.assignee_names.length > 0
                      ? task.assignee_names
                          .map(
                            (name, index) => `
                          <div class="d-flex align-items-center justify-content-between mb-2">
                            <div class="d-flex align-items-center">
                              <div class="user-avatar me-2">
                                ${name
                                  .split(" ")
                                  .map((n) => n[0])
                                  .join("")
                                  .toUpperCase()}
                              </div>
                              <span>${name}</span>
                            </div>
                            ${
                              (task.owner_id && window.currentUserId && task.owner_id == window.currentUserId) ||
                              (task.creator_id && window.currentUserId && task.creator_id == window.currentUserId)
                                ? `<button type="button" class="btn btn-outline-danger btn-sm remove-assignee-btn" 
                                          data-user-id="${task.assignee_ids[index]}" 
                                          data-user-name="${name}" 
                                          title="Remove ${name} from this task">
                                    <i class="bi bi-x"></i>
                                  </button>`
                                : ''
                            }
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
      // Add event handlers for remove assignee buttons
      document.querySelectorAll('.remove-assignee-btn').forEach(function(btn) {
        btn.addEventListener('click', async function(e) {
          e.preventDefault();
          
          const userId = this.getAttribute('data-user-id');
          const userName = this.getAttribute('data-user-name');
          
          if (!confirm(`Are you sure you want to remove ${userName} from this task?`)) {
            return;
          }
          
          // Disable button during request
          this.disabled = true;
          const originalText = this.innerHTML;
          this.innerHTML = '<i class="bi bi-hourglass-split"></i>';
          
          try {
            // Remove user from assignees list
            const currentAssignees = task.assignee_ids || [];
            const newAssignees = currentAssignees.filter(id => id != userId);
            
            console.log('[DEBUG] Removing user from task:', {
              taskId: task.id,
              userId: userId,
              userName: userName,
              currentAssignees: currentAssignees,
              newAssignees: newAssignees
            });
            
            const response = await fetch(`/api/tasks/${task.id}`, {
              method: 'PATCH',
              headers: {
                'Content-Type': 'application/json',
              },
              credentials: 'include',
              body: JSON.stringify({ assignees: newAssignees })
            });
            
            if (!response.ok) {
              throw new Error('Failed to remove assignee');
            }
            
            // Update task object
            task.assignee_ids = newAssignees;
            task.assignee_names = task.assignee_names.filter((name, index) => 
              task.assignee_ids.indexOf(parseInt(userId)) === -1 || index !== task.assignee_names.indexOf(userName)
            );
            
            // Update the assigned members display
            const assignedMembersContent = document.getElementById('assignedMembersContent');
            if (assignedMembersContent) {
              assignedMembersContent.innerHTML = `
                ${
                  task.assignee_names && task.assignee_names.length > 0
                    ? task.assignee_names
                        .map(
                          (name, index) => `
                        <div class="d-flex align-items-center justify-content-between mb-2">
                          <div class="d-flex align-items-center">
                            <div class="user-avatar me-2">
                              ${name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")
                                .toUpperCase()}
                            </div>
                            <span>${name}</span>
                          </div>
                          ${
                            (task.owner_id && window.currentUserId && task.owner_id == window.currentUserId) ||
                            (task.creator_id && window.currentUserId && task.creator_id == window.currentUserId)
                              ? `<button type="button" class="btn btn-outline-danger btn-sm remove-assignee-btn" 
                                        data-user-id="${task.assignee_ids[index]}" 
                                        data-user-name="${name}" 
                                        title="Remove ${name} from this task">
                                  <i class="bi bi-x"></i>
                                </button>`
                              : ''
                          }
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
              `;
              
              // Re-add event handlers for the new remove buttons
              assignedMembersContent.querySelectorAll('.remove-assignee-btn').forEach(function(newBtn) {
                newBtn.addEventListener('click', arguments.callee);
              });
            }
            
            // Show success message
            const successMsg = document.createElement('div');
            successMsg.className = 'alert alert-success alert-dismissible fade show mt-2';
            successMsg.innerHTML = `
              <strong>Success!</strong> ${userName} has been removed from this task.
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Insert success message after the assigned members content
            assignedMembersContent.parentNode.insertBefore(successMsg, assignedMembersContent.nextSibling);
            
            // Auto-dismiss after 3 seconds
            setTimeout(() => {
              if (successMsg.parentNode) {
                successMsg.remove();
              }
            }, 3000);
            
          } catch (error) {
            console.error('Error removing assignee:', error);
            alert('Failed to remove assignee. Please try again.');
          } finally {
            // Re-enable button
            this.disabled = false;
            this.innerHTML = originalText;
          }
        });
      });
      
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
        
        // Add event handler for Assign button
        assignBtn.addEventListener('click', async function(e) {
          e.preventDefault();
          console.log('[DEBUG] Assign button clicked');
          
          const assigneeSection = document.querySelector('#changeAssigneesBtn').closest('.task-section');
          const assigneeContent = assigneeSection.querySelector('.section-content');
          
          // Show loading state
          assigneeContent.innerHTML = `
            <div class="text-center py-2">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <span class="ms-2">Loading available members...</span>
            </div>
          `;
          
          try {
            // Fetch available members from API
            const projectId = getProjectIdFromUrl();
            const response = await fetch(`/projects/${projectId}/tasks/${task.id}/unassigned-members`, {
              credentials: 'include'
            });
            
            if (!response.ok) {
              throw new Error('Failed to fetch available members');
            }
            
            const data = await response.json();
            const availableMembers = data.unassigned_members || [];
            
            console.log('[DEBUG] Available members:', availableMembers);
            
            // Create assignment interface
            let assignmentHTML = '';
            
            if (availableMembers.length === 0) {
              assignmentHTML = `
                <div class="alert alert-info">
                  <i class="bi bi-info-circle me-2"></i>
                  There are no available members to assign to this task.
                </div>
                <div class="d-flex justify-content-end mt-3">
                  <button type="button" class="btn btn-secondary btn-sm" id="cancelAssignBtn">Cancel</button>
                </div>
              `;
            } else {
              assignmentHTML = `
                <div class="mb-3">
                  <label class="form-label fw-bold">Select Member *</label>
                  <select class="form-select" id="memberToAssignSelect">
                    <option value="">Choose a member...</option>
                    ${availableMembers.map(member => 
                      `<option value="${member.id}">${member.name} (${member.email})</option>`
                    ).join('')}
                  </select>
                </div>
                <div class="d-flex justify-content-end gap-2">
                  <button type="button" class="btn btn-secondary btn-sm" id="cancelAssignBtn">Cancel</button>
                  <button type="button" class="btn btn-primary btn-sm" id="applyAssignBtn">Apply</button>
                </div>
              `;
            }
            
            assigneeContent.innerHTML = assignmentHTML;
            
            // Add event handlers
            document.getElementById('cancelAssignBtn').addEventListener('click', function() {
              // Restore original assignee display
              const assignedMembersContent = document.getElementById('assignedMembersContent');
              assignedMembersContent.innerHTML = `
                ${
                  task.assignee_names && task.assignee_names.length > 0
                    ? task.assignee_names
                        .map(
                          (name, index) => `
                        <div class="d-flex align-items-center justify-content-between mb-2">
                          <div class="d-flex align-items-center">
                            <div class="user-avatar me-2">
                              ${name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")
                                .toUpperCase()}
                            </div>
                            <span>${name}</span>
                          </div>
                          ${
                            (task.owner_id && window.currentUserId && task.owner_id == window.currentUserId) ||
                            (task.creator_id && window.currentUserId && task.creator_id == window.currentUserId)
                              ? `<button type="button" class="btn btn-outline-danger btn-sm remove-assignee-btn" 
                                        data-user-id="${task.assignee_ids[index]}" 
                                        data-user-name="${name}" 
                                        title="Remove ${name} from this task">
                                  <i class="bi bi-x"></i>
                                </button>`
                              : ''
                          }
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
              `;
              
              // Re-add event handlers for remove buttons
              assignedMembersContent.querySelectorAll('.remove-assignee-btn').forEach(function(btn) {
                btn.addEventListener('click', async function(e) {
                  e.preventDefault();
                  
                  const userId = this.getAttribute('data-user-id');
                  const userName = this.getAttribute('data-user-name');
                  
                  if (!confirm(`Are you sure you want to remove ${userName} from this task?`)) {
                    return;
                  }
                  
                  // Disable button during request
                  this.disabled = true;
                  const originalText = this.innerHTML;
                  this.innerHTML = '<i class="bi bi-hourglass-split"></i>';
                  
                  try {
                    // Remove user from assignees list
                    const currentAssignees = task.assignee_ids || [];
                    const newAssignees = currentAssignees.filter(id => id != userId);
                    
                    const response = await fetch(`/api/tasks/${task.id}`, {
                      method: 'PATCH',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      credentials: 'include',
                      body: JSON.stringify({ assignees: newAssignees })
                    });
                    
                    if (!response.ok) {
                      throw new Error('Failed to remove assignee');
                    }
                    
                    // Update task object
                    task.assignee_ids = newAssignees;
                    task.assignee_names = task.assignee_names.filter(name => name !== userName);
                    
                    // Reload task details to refresh the display
                    await loadTaskDetails(task.id);
                    
                  } catch (error) {
                    console.error('Error removing assignee:', error);
                    alert('Failed to remove assignee. Please try again.');
                  } finally {
                    // Re-enable button
                    this.disabled = false;
                    this.innerHTML = originalText;
                  }
                });
              });
            });
            
            const applyBtn = document.getElementById('applyAssignBtn');
            if (applyBtn) {
              applyBtn.addEventListener('click', async function() {
                const selectedMemberId = document.getElementById('memberToAssignSelect').value;
                
                if (!selectedMemberId) {
                  alert('Please select a member to assign.');
                  return;
                }
                
                // Disable button during request
                applyBtn.disabled = true;
                applyBtn.textContent = 'Assigning...';
                
                try {
                  // Get current assignees and add the new one
                  const currentAssignees = task.assignee_ids || [];
                  const newAssignees = [...currentAssignees, parseInt(selectedMemberId)];
                  
                  console.log('[DEBUG] PATCH /api/tasks/' + task.id, { assignees: newAssignees });
                  
                  const patchResponse = await fetch(`/api/tasks/${task.id}`, {
                    method: 'PATCH',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({ assignees: newAssignees })
                  });
                  
                  if (!patchResponse.ok) {
                    throw new Error('Failed to assign member');
                  }
                  
                  // Find the selected member's name
                  const selectedMember = availableMembers.find(m => m.id == selectedMemberId);
                  
                  // Update the task object with new assignee
                  if (selectedMember) {
                    task.assignee_ids = newAssignees;
                    task.assignee_names = [...(task.assignee_names || []), selectedMember.name];
                  }
                  
                  // Update the display with new assignee
                  const assignedMembersContent = document.getElementById('assignedMembersContent');
                  assignedMembersContent.innerHTML = `
                    ${
                      task.assignee_names && task.assignee_names.length > 0
                        ? task.assignee_names
                            .map(
                              (name, index) => `
                            <div class="d-flex align-items-center justify-content-between mb-2">
                              <div class="d-flex align-items-center">
                                <div class="user-avatar me-2">
                                  ${name
                                    .split(" ")
                                    .map((n) => n[0])
                                    .join("")
                                    .toUpperCase()}
                                </div>
                                <span>${name}</span>
                              </div>
                              ${
                                (task.owner_id && window.currentUserId && task.owner_id == window.currentUserId) ||
                                (task.creator_id && window.currentUserId && task.creator_id == window.currentUserId)
                                  ? `<button type="button" class="btn btn-outline-danger btn-sm remove-assignee-btn" 
                                            data-user-id="${task.assignee_ids[index]}" 
                                            data-user-name="${name}" 
                                            title="Remove ${name} from this task">
                                      <i class="bi bi-x"></i>
                                    </button>`
                                  : ''
                              }
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
                  `;
                  
                  // Re-add event handlers for remove buttons
                  assignedMembersContent.querySelectorAll('.remove-assignee-btn').forEach(function(btn) {
                    btn.addEventListener('click', async function(e) {
                      e.preventDefault();
                      
                      const userId = this.getAttribute('data-user-id');
                      const userName = this.getAttribute('data-user-name');
                      
                      if (!confirm(`Are you sure you want to remove ${userName} from this task?`)) {
                        return;
                      }
                      
                      // Disable button during request
                      this.disabled = true;
                      const originalText = this.innerHTML;
                      this.innerHTML = '<i class="bi bi-hourglass-split"></i>';
                      
                      try {
                        // Remove user from assignees list
                        const currentAssignees = task.assignee_ids || [];
                        const newAssignees = currentAssignees.filter(id => id != userId);
                        
                        const response = await fetch(`/api/tasks/${task.id}`, {
                          method: 'PATCH',
                          headers: {
                            'Content-Type': 'application/json',
                          },
                          credentials: 'include',
                          body: JSON.stringify({ assignees: newAssignees })
                        });
                        
                        if (!response.ok) {
                          throw new Error('Failed to remove assignee');
                        }
                        
                        // Update task object
                        task.assignee_ids = newAssignees;
                        task.assignee_names = task.assignee_names.filter(name => name !== userName);
                        
                        // Reload task details to refresh the display
                        await loadTaskDetails(task.id);
                        
                      } catch (error) {
                        console.error('Error removing assignee:', error);
                        alert('Failed to remove assignee. Please try again.');
                      } finally {
                        // Re-enable button
                        this.disabled = false;
                        this.innerHTML = originalText;
                      }
                    });
                  });
                  
                  // Show success message
                  const successMsg = document.createElement('div');
                  successMsg.className = 'alert alert-success alert-dismissible fade show mt-2';
                  successMsg.innerHTML = `
                    <strong>Success!</strong> Member assigned successfully.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                  `;
                  
                  // Insert success message after the assignee content
                  assignedMembersContent.parentNode.insertBefore(successMsg, assignedMembersContent.nextSibling);
                  
                  // Auto-dismiss after 3 seconds
                  setTimeout(() => {
                    if (successMsg.parentNode) {
                      successMsg.remove();
                    }
                  }, 3000);
                  
                } catch (error) {
                  console.error('Error assigning member:', error);
                  alert('Failed to assign member. Please try again.');
                } finally {
                  // Re-enable button
                  applyBtn.disabled = false;
                  applyBtn.textContent = 'Apply';
                }
              });
            }
            
          } catch (error) {
            console.error('Error fetching available members:', error);
            assigneeContent.innerHTML = `
              <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                Failed to load available members. Please try again.
              </div>
              <div class="d-flex justify-content-end mt-3">
                <button type="button" class="btn btn-secondary btn-sm" id="cancelAssignBtn">Cancel</button>
              </div>
            `;
            
            // Add cancel handler for error case
            document.getElementById('cancelAssignBtn').addEventListener('click', function() {
              // Restore original assignee display
              const assignedMembersContent = document.getElementById('assignedMembersContent');
              assignedMembersContent.innerHTML = `
                ${
                  task.assignee_names && task.assignee_names.length > 0
                    ? task.assignee_names
                        .map(
                          (name, index) => `
                        <div class="d-flex align-items-center justify-content-between mb-2">
                          <div class="d-flex align-items-center">
                            <div class="user-avatar me-2">
                              ${name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")
                                .toUpperCase()}
                            </div>
                            <span>${name}</span>
                          </div>
                          ${
                            (task.owner_id && window.currentUserId && task.owner_id == window.currentUserId) ||
                            (task.creator_id && window.currentUserId && task.creator_id == window.currentUserId)
                              ? `<button type="button" class="btn btn-outline-danger btn-sm remove-assignee-btn" 
                                        data-user-id="${task.assignee_ids[index]}" 
                                        data-user-name="${name}" 
                                        title="Remove ${name} from this task">
                                  <i class="bi bi-x"></i>
                                </button>`
                              : ''
                          }
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
              `;
              
              // Re-add event handlers for remove buttons
              assignedMembersContent.querySelectorAll('.remove-assignee-btn').forEach(function(btn) {
                btn.addEventListener('click', async function(e) {
                  e.preventDefault();
                  
                  const userId = this.getAttribute('data-user-id');
                  const userName = this.getAttribute('data-user-name');
                  
                  if (!confirm(`Are you sure you want to remove ${userName} from this task?`)) {
                    return;
                  }
                  
                  // Disable button during request
                  this.disabled = true;
                  const originalText = this.innerHTML;
                  this.innerHTML = '<i class="bi bi-hourglass-split"></i>';
                  
                  try {
                    // Remove user from assignees list
                    const currentAssignees = task.assignee_ids || [];
                    const newAssignees = currentAssignees.filter(id => id != userId);
                    
                    const response = await fetch(`/api/tasks/${task.id}`, {
                      method: 'PATCH',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      credentials: 'include',
                      body: JSON.stringify({ assignees: newAssignees })
                    });
                    
                    if (!response.ok) {
                      throw new Error('Failed to remove assignee');
                    }
                    
                    // Update task object
                    task.assignee_ids = newAssignees;
                    task.assignee_names = task.assignee_names.filter(name => name !== userName);
                    
                    // Reload task details to refresh the display
                    await loadTaskDetails(task.id);
                    
                  } catch (error) {
                    console.error('Error removing assignee:', error);
                    alert('Failed to remove assignee. Please try again.');
                  } finally {
                    // Re-enable button
                    this.disabled = false;
                    this.innerHTML = originalText;
                  }
                });
              });
            });
          }
        });
      }
    }, 0);

    // Add event handler for Status & Priority Change button
    setTimeout(function() {
      const changeBtn = document.getElementById('changeStatusPriorityBtn');
      if (changeBtn) {
        changeBtn.addEventListener('click', async function(e) {
          e.preventDefault();
          
          const statusDropdown = document.getElementById('taskStatusDropdown');
          const priorityDropdown = document.getElementById('taskPriorityDropdown');
          
          if (!statusDropdown || !priorityDropdown) {
            console.error('Status or Priority dropdown not found');
            return;
          }
          
          const newStatus = statusDropdown.value;
          const newPriority = priorityDropdown.value;
          
          // Map frontend values to backend enum values
          const statusMap = {
            'NOT_STARTED': 'Not Started',
            'IN_PROGRESS': 'In Progress',
            'BLOCKED': 'Blocked',
            'COMPLETED': 'Completed',
            'CANCELLED': 'Cancelled'
          };
          
          const priorityMap = {
            'LOW': 'Low',
            'MEDIUM': 'Medium',
            'HIGH': 'High',
            'URGENT': 'Urgent'
          };
          
          // Disable button during request
          changeBtn.disabled = true;
          changeBtn.textContent = 'Updating...';
          
          try {
            const response = await fetch(`/api/tasks/${task.id}`, {
              method: 'PATCH',
              headers: {
                'Content-Type': 'application/json',
              },
              credentials: 'include',
              body: JSON.stringify({
                status: statusMap[newStatus] || newStatus,
                priority: priorityMap[newPriority] || newPriority
              })
            });
            
            if (response.ok) {
              // Update the task badges in the header
              const statusBadge = document.querySelector('.task-badges .badge:first-child');
              const priorityBadge = document.querySelector('.task-badges .badge:last-child');
              
              if (statusBadge) {
                const displayStatus = statusMap[newStatus] || newStatus;
                statusBadge.className = `badge ${getStatusClass(displayStatus)} me-2`;
                statusBadge.textContent = displayStatus;
              }
              
              if (priorityBadge) {
                const displayPriority = priorityMap[newPriority] || newPriority;
                priorityBadge.className = `badge ${getPriorityClass(displayPriority)}`;
                priorityBadge.textContent = displayPriority;
              }
              
              // Show success message
              const successMsg = document.createElement('div');
              successMsg.className = 'alert alert-success alert-dismissible fade show mt-2';
              successMsg.innerHTML = `
                <strong>Success!</strong> Status and priority updated successfully.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
              `;
              
              // Insert success message after the Change button
              changeBtn.parentNode.insertBefore(successMsg, changeBtn.nextSibling);
              
              // Auto-dismiss after 3 seconds
              setTimeout(() => {
                if (successMsg.parentNode) {
                  successMsg.remove();
                }
              }, 3000);
              
            } else {
              const errorData = await response.json();
              alert('Failed to update task: ' + (errorData.message || 'Unknown error'));
            }
          } catch (error) {
            console.error('Error updating task:', error);
            alert('An error occurred while updating the task. Please try again.');
          } finally {
            // Re-enable button
            changeBtn.disabled = false;
            changeBtn.textContent = 'Change';
          }
        });
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
 * Initialize Files Tab functionality
 */
function initializeFilesTab() {
  console.log('🔧 [DEBUG] Initializing Files tab...');
  
  const filesTab = document.getElementById('files-tab');
  if (!filesTab) {
    console.warn('⚠️ [DEBUG] Files tab not found');
    return;
  }
  
  // Load files when tab is shown
  filesTab.addEventListener('shown.bs.tab', function() {
    console.log('📁 [DEBUG] Files tab activated, loading project files...');
    loadProjectFiles();
  });
  
  async function loadProjectFiles() {
    const projectId = getProjectIdFromUrl();
    if (!projectId) {
      console.error('❌ [DEBUG] No project ID found');
      return;
    }
    
    try {
      // Show loading state
      const tableBody = document.querySelector('#files table tbody');
      if (tableBody) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="6" class="text-center py-4">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <div class="mt-2">Loading files...</div>
            </td>
          </tr>
        `;
      }
      
      console.log('🌐 [DEBUG] Fetching files from:', `/projects/${projectId}/files`);
      
      const response = await fetch(`/projects/${projectId}/files`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('📁 [DEBUG] Files loaded:', data);
      
      displayProjectFiles(data.files || []);
      
    } catch (error) {
      console.error('❌ [DEBUG] Error loading project files:', error);
      const tableBody = document.querySelector('#files table tbody');
      if (tableBody) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="6" class="text-center py-4">
              <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                Failed to load files. Please try again.
              </div>
            </td>
          </tr>
        `;
      }
    }
  }
  
  function displayProjectFiles(files) {
    const tableBody = document.querySelector('#files table tbody');
    if (!tableBody) {
      console.error('❌ [DEBUG] Files table body not found');
      return;
    }
    
    if (files.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4">
            <div class="text-muted">
              <i class="bi bi-folder" style="font-size: 2rem;"></i>
              <p class="mb-0 mt-2">No files uploaded yet.</p>
              <small>Files will appear here when uploaded to tasks.</small>
            </div>
          </td>
        </tr>
      `;
      return;
    }
    
    let html = '';
    files.forEach(file => {
      const uploadDate = file.created_at ? new Date(file.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      }) : 'Unknown';
      
      html += `
        <tr>
          <td>
            <div class="d-flex align-items-center">
              <i class="${file.file_icon} ${file.file_color} me-2" style="font-size: 1.5rem"></i>
              <div>
                <div class="fw-medium">${file.file_name}</div>
                <small class="text-muted">Task: <a href="#" onclick="showTaskDetails(${file.task_id})">${file.task_name}</a></small>
              </div>
            </div>
          </td>
          <td>
            <span class="badge bg-light text-dark">${file.mime_type}</span>
          </td>
          <td>${file.file_size_formatted}</td>
          <td>
            <div class="d-flex align-items-center">
              <div class="user-avatar-small me-2">
                ${file.uploader_name.split(' ').map(n => n[0]).join('').toUpperCase()}
              </div>
              ${file.uploader_name}
            </div>
          </td>
          <td>${uploadDate}</td>
          <td>
            <div class="btn-group" role="group">
              <a href="${file.download_url}" target="_blank" class="btn btn-sm btn-outline-primary" title="Download">
                <i class="bi bi-download"></i>
              </a>
              <button class="btn btn-sm btn-outline-info" onclick="showTaskDetails(${file.task_id})" title="View Task">
                <i class="bi bi-eye"></i>
              </button>
              <button class="btn btn-sm btn-outline-danger" onclick="deleteProjectFile(${file.id})" title="Delete">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    });
    
    tableBody.innerHTML = html;
  }
  
  // Global function to show task details from files tab
  window.showTaskDetails = function(taskId) {
    // Switch to tasks tab first
    const tasksTab = document.getElementById('tasks-tab');
    if (tasksTab) {
      const tab = new bootstrap.Tab(tasksTab);
      tab.show();
      
      // Wait a bit for tab transition, then show task details
      setTimeout(() => {
        if (window.loadTaskDetails) {
          window.loadTaskDetails(taskId);
        }
      }, 300);
    }
  };
  
  // Global function to delete project file
  window.deleteProjectFile = async function(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    try {
      const response = await fetch(`/api/attachments/${fileId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete file');
      }
      
      console.log('✅ [DEBUG] File deleted successfully');
      
      // Reload files
      loadProjectFiles();
      
    } catch (error) {
      console.error('❌ [DEBUG] Error deleting file:', error);
      alert('Failed to delete file. Please try again.');
    }
  };
}
