// --- Comment System: Render, Sanitize, and Attachments ---
// Escape HTML utility
function escapeHTML(str) {
  return (str || '').replace(/[&<>"']/g, function(tag) {
    const charsToReplace = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    };
    return charsToReplace[tag] || tag;
  });
}

// Render a single comment (text + attachments)
function renderCommentItem(comment) {
  const userName = comment.user?.name || 'User';
  const createdAt = new Date(comment.created_at).toLocaleString();
  const content = escapeHTML(comment.content || '').replace(/\n/g, '<br>');
  let html = `<div class="comment mb-3 p-2 border rounded">
    <div class="d-flex align-items-center mb-1">
      <div class="fw-bold me-2">${escapeHTML(userName)}</div>
      <span class="text-muted small">${createdAt}</span>
    </div>
    <div class="mb-1 comment-text">${content}</div>`;
  if (comment.attachments && comment.attachments.length > 0) {
    html += '<div class="comment-attachments mb-1 d-flex flex-wrap">';
    for (const a of comment.attachments) {
      let url = a.url || a.file_path || '';
      if (url && !url.startsWith('http')) url = 'http://localhost:4001' + url;
      if ((a.mime_type || a.mimetype || '').startsWith('image/')) {
        html += `<a href="${url}" target="_blank" class="me-2 mb-2"><img src="${url}" style="max-width:80px;max-height:80px;border-radius:6px;border:1px solid #ccc;object-fit:cover;" alt="${escapeHTML(a.file_name || a.filename || '')}"></a>`;
      } else {
        const fname = escapeHTML(a.file_name || a.filename || 'file');
        html += `<div class="me-2 mb-2"><i class="bi bi-paperclip"></i> <a href="${url}" target="_blank">${fname}</a></div>`;
      }
    }
    html += '</div>';
  }
  html += '</div>';
  return html;
}

// Render all comments for a task
async function loadCommentsForTask(taskId) {
  const commentsArea = document.querySelector('.comments-area');
  if (!commentsArea) return;
  // Always keep the comment form at the top
  let commentForm = commentsArea.querySelector('.comment-form');
  if (!commentForm) {
    // If not present, create and insert it
    commentForm = document.createElement('div');
    commentForm.className = 'comment-form mb-3';
    commentForm.innerHTML = `
      <textarea class="form-control" rows="3" placeholder="Add a comment..."></textarea>
      <div class="d-flex justify-content-end mt-2">
        <button class="btn btn-primary btn-sm">
          <i class="bi bi-send me-1"></i>Post Comment
        </button>
      </div>
    `;
    commentsArea.prepend(commentForm);
    // (Re-)initialize comment form logic
    if (typeof initializeCommentForm === 'function') {
      initializeCommentForm(taskId);
    }
  }
  // Remove all comments except the form
  Array.from(commentsArea.children).forEach(child => {
    if (!child.classList.contains('comment-form')) child.remove();
  });
  // Show loading state
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'text-center text-muted py-3';
  loadingDiv.innerHTML = '<i class="bi bi-chat-dots" style="font-size: 2rem;"></i><p class="mb-0 mt-2">Loading comments...</p>';
  commentsArea.appendChild(loadingDiv);
  try {
    const res = await fetch(`/api/tasks/${taskId}/comments`, { credentials: 'include' });
    if (!res.ok) throw new Error('Failed to fetch comments');
    const comments = await res.json();
    loadingDiv.remove();
    if (!comments.length) {
      const emptyDiv = document.createElement('div');
      emptyDiv.className = 'text-center text-muted py-3';
      emptyDiv.innerHTML = '<i class="bi bi-chat-dots" style="font-size: 2rem;"></i><p class="mb-0 mt-2">No comments yet. Be the first to add one!</p>';
      commentsArea.appendChild(emptyDiv);
      updateCommentCountBadge(0);
      return;
    }
    for (const c of comments) {
      commentsArea.appendChild(document.createRange().createContextualFragment(renderCommentItem(c)));
    }
    updateCommentCountBadge(comments.length);
  } catch (err) {
    loadingDiv.remove();
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger mt-2';
    errorDiv.textContent = 'Failed to load comments.';
    commentsArea.appendChild(errorDiv);
  }
}

// Add a new comment to the list (after posting)
function addNewCommentToList(comment) {
  const commentsArea = document.querySelector('.comments-area');
  if (!commentsArea) return;
  // Remove empty state if present
  commentsArea.querySelector('.text-center.text-muted')?.remove();
  commentsArea.insertAdjacentHTML('beforeend', renderCommentItem(comment));
  updateCommentCountBadge();
}

// Update the comment count badge
function updateCommentCountBadge(count) {
  const badge = document.querySelector('.comment-count-badge');
  if (badge) {
    if (typeof count === 'undefined') {
      // Try to count rendered comments
      const commentsArea = document.querySelector('.comments-area');
      if (commentsArea) {
        count = commentsArea.querySelectorAll('.comment').length;
      } else {
        count = 0;
      }
    }
    badge.textContent = count;
  }
}
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
              <span class="badge bg-secondary ms-2 comment-count-badge">0</span>
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

    // Initialize attachment handlers after modal is rendered
    setTimeout(function() {
      initializeAttachmentHandlers(task);
      // Initialize comment form logic for this task
      initializeCommentForm(task.id);
      // Load and render comments for this task
      loadCommentsForTask(task.id);
    }, 0);
// --- Comment Form Logic ---
function initializeCommentForm(taskId) {
  // Always select the latest visible .comment-form in the modal (avoid old handlers)
  const forms = document.querySelectorAll('.comment-form');
  let form = null;
  if (forms.length === 1) {
    form = forms[0];
  } else if (forms.length > 1) {
    // Pick the one that is visible (not display:none)
    form = Array.from(forms).find(f => f.offsetParent !== null);
  }
  if (!form) return;
  // Remove any previous submit handler to avoid double submit
  form.onsubmit = null;
  // Remove any previous click handler on the send button
  const textarea = form.querySelector('textarea');
  const sendBtn = form.querySelector('button.btn-primary');
  if (sendBtn) {
    sendBtn.onclick = null;
  }
  // Attachment preview area
  let previewArea = form.querySelector('.comment-attachment-preview');
  if (!previewArea) {
    previewArea = document.createElement('div');
    previewArea.className = 'comment-attachment-preview d-flex flex-wrap mb-2';
    form.insertBefore(previewArea, form.querySelector('.d-flex'));
  }
  let attachments = [];
  let uploading = false;
  // Helper: update send button state
  function updateSendBtn() {
    sendBtn.disabled = uploading || (!textarea.value.trim() && attachments.length === 0);
  }
  // Helper: render attachment preview
  function renderPreview() {
    previewArea.innerHTML = '';
    attachments.forEach((file, idx) => {
      const isImage = file.type && file.type.startsWith('image/');
      const url = file.previewUrl || '';
      const el = document.createElement('div');
      el.className = 'me-2 mb-2 position-relative';
      if (isImage && url) {
        el.innerHTML = `<img src="${url}" alt="${escapeHTML(file.name)}" class="img-thumbnail" style="max-width:60px;max-height:60px;object-fit:cover;">`;
      } else {
        el.innerHTML = `<div class="border rounded bg-light px-2 py-1 small"><i class="bi bi-paperclip me-1"></i>${escapeHTML(file.name)}</div>`;
      }
      // Remove button
      const rmBtn = document.createElement('button');
      rmBtn.type = 'button';
      rmBtn.className = 'btn btn-sm btn-danger position-absolute top-0 end-0 p-0 m-0';
      rmBtn.style.width = '18px';
      rmBtn.style.height = '18px';
      rmBtn.innerHTML = '<i class="bi bi-x"></i>';
      rmBtn.onclick = () => {
        attachments.splice(idx, 1);
        renderPreview();
        updateSendBtn();
      };
      el.appendChild(rmBtn);
      previewArea.appendChild(el);
    });
  }
  // File input for attachments
  let fileInput = form.querySelector('input[type="file"]');
  if (!fileInput) {
    fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.multiple = true;
    fileInput.accept = '.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.jpg,.jpeg,.png,.gif,.mp4,.mov,.avi';
    fileInput.style.display = 'none';
    form.appendChild(fileInput);
  }
  // Add file via file input
  fileInput.addEventListener('change', e => {
    for (const file of Array.from(e.target.files)) {
      if (file.size > 10 * 1024 * 1024) continue;
      file.previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : '';
      attachments.push(file);
    }
    renderPreview();
    updateSendBtn();
    fileInput.value = '';
  });
  // Add file via paste
  textarea.addEventListener('paste', e => {
    if (e.clipboardData && e.clipboardData.files.length > 0) {
      for (const file of Array.from(e.clipboardData.files)) {
        if (file.size > 10 * 1024 * 1024) continue;
        file.previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : '';
        attachments.push(file);
      }
      renderPreview();
      updateSendBtn();
      e.preventDefault();
    }
  });
  // Add file via drag-drop
  form.addEventListener('dragover', e => {
    e.preventDefault();
    form.classList.add('drag-over');
  });
  form.addEventListener('dragleave', e => {
    e.preventDefault();
    form.classList.remove('drag-over');
  });
  form.addEventListener('drop', e => {
    e.preventDefault();
    form.classList.remove('drag-over');
    if (e.dataTransfer && e.dataTransfer.files.length > 0) {
      for (const file of Array.from(e.dataTransfer.files)) {
        if (file.size > 10 * 1024 * 1024) continue;
        file.previewUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : '';
        attachments.push(file);
      }
      renderPreview();
      updateSendBtn();
    }
  });
  // Click to open file input
  previewArea.addEventListener('click', e => {
    if (e.target === previewArea) fileInput.click();
  });
  // Add a button to open file input
  let addBtn = form.querySelector('.add-attachment-btn');
  if (!addBtn) {
    addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className = 'btn btn-outline-secondary btn-sm add-attachment-btn mb-2';
    addBtn.innerHTML = '<i class="bi bi-paperclip"></i> Add file';
    form.insertBefore(addBtn, previewArea);
  }
  addBtn.onclick = () => fileInput.click();
  // Send button logic
  textarea.addEventListener('input', updateSendBtn);
  updateSendBtn();
  // Post comment handler (works for both Enter and button click)
  async function handleCommentSubmit(e) {
    if (e) e.preventDefault();
    if (uploading) return;
    uploading = true;
    updateSendBtn();
    sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Posting...';
    sendBtn.disabled = true;
    // Debug: log submit event
    console.debug('[CommentForm] Submitting comment', { text: textarea.value, attachments });
    // Upload attachments to CDN first
    let uploadedAttachmentIds = [];
    let errorMsg = '';
    if (attachments.length > 0) {
      for (const file of attachments) {
        if (file.size > 10 * 1024 * 1024) {
          errorMsg = `File ${escapeHTML(file.name)} is too large.`;
          continue;
        }
        const formData = new FormData();
        formData.append('file', file);
        try {
          const res = await fetch('http://localhost:4001/upload', { method: 'POST', body: formData });
          if (!res.ok) throw new Error('Upload failed');
          const data = await res.json();
          if (!data.id) throw new Error('No id returned');
          uploadedAttachmentIds.push(data.id);
        } catch (err) {
          errorMsg = `Failed to upload ${escapeHTML(file.name)}`;
        }
      }
    }
    // Post comment
    try {
      // Build payload according to backend schema: content, task_id, user_id, attachment_ids (if any)
      const payload = {
        content: textarea.value.trim(),
        task_id: taskId,
        user_id: window.currentUserId
      };
      if (uploadedAttachmentIds.length > 0) {
        payload.attachment_ids = uploadedAttachmentIds;
      }
      const res = await fetch(`/api/tasks/${taskId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        // Try to extract error message from backend
        let msg = 'Failed to post comment.';
        try {
          const errData = await res.json();
          if (errData && errData.detail) msg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        } catch {}
        throw new Error(msg);
      }
      let comment = await res.json();
      // If comment is an array, take the first element (defensive, backend bug)
      if (Array.isArray(comment)) comment = comment[0];
      // Defensive: if comment is an object with only one key and that key is an array, use that array's first element
      if (comment && typeof comment === 'object' && Object.keys(comment).length === 1) {
        const val = comment[Object.keys(comment)[0]];
        if (Array.isArray(val)) comment = val[0];
      }
      // If comment is still not an object, show error
      if (!comment || typeof comment !== 'object') {
        throw new Error('Invalid comment response from server.');
      }
      addNewCommentToList(comment);
      textarea.value = '';
      attachments = [];
      renderPreview();
      errorMsg = '';
    } catch (err) {
      errorMsg = err.message || 'Failed to post comment.';
    }
    // Show error if any
    let errorArea = form.querySelector('.comment-error-msg');
    if (!errorArea) {
      errorArea = document.createElement('div');
      errorArea.className = 'comment-error-msg text-danger small mt-1';
      form.insertBefore(errorArea, previewArea.nextSibling);
    }
    errorArea.textContent = errorMsg;
    if (!errorMsg) errorArea.textContent = '';
    uploading = false;
    sendBtn.innerHTML = '<i class="bi bi-send me-1"></i>Post Comment';
    updateSendBtn();
    textarea.focus();
  }

  // Attach both submit and click handler for robustness
  form.onsubmit = handleCommentSubmit;
  if (sendBtn) {
    sendBtn.onclick = function(e) {
      // Only trigger if not disabled
      if (!sendBtn.disabled) {
        handleCommentSubmit(e);
      }
    };
  }
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
      
      console.log('🌐 [DEBUG] Fetching files from:', `/api/projects/${projectId}/files`);
      const response = await fetch(`/api/projects/${projectId}/files`, {
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
      // Detect if file is image
      const isImage = file.mime_type && file.mime_type.startsWith('image/');
      html += `
        <tr>
          <td>
            <div class="d-flex align-items-center">
              <i class="${file.file_icon} ${file.file_color} me-2" style="font-size: 1.5rem"></i>
              <div>
                <div class="fw-medium">
                  <a href="#" class="file-link" data-url="${file.download_url}" data-mime="${file.mime_type}" data-name="${file.file_name}">${file.file_name}</a>
                </div>
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

    // Add click handler for file links (image preview or open)
    tableBody.querySelectorAll('.file-link').forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        const url = this.getAttribute('data-url');
        const mime = this.getAttribute('data-mime');
        const name = this.getAttribute('data-name');
        if (mime && mime.startsWith('image/')) {
          showImagePreviewModal(url, name);
        } else {
          window.open(url, '_blank');
        }
      });
    });
  }

// Image preview modal logic
function showImagePreviewModal(url, name) {
  let modal = document.getElementById('imagePreviewModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'imagePreviewModal';
    modal.className = 'modal fade';
    modal.tabIndex = -1;
    modal.innerHTML = `
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${name}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center">
            <img src="${url}" alt="${name}" class="img-fluid rounded shadow" style="max-height:60vh; max-width:100%; object-fit:contain;" />
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  } else {
    modal.querySelector('.modal-title').textContent = name;
    modal.querySelector('img').src = url;
    modal.querySelector('img').alt = name;
  }
  // Show modal using Bootstrap
  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();
}
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
// End of displayProjectFiles and image preview modal logic

/**
 * Initialize attachment handlers for task modal
 */
function initializeAttachmentHandlers(task) {
  console.log('[DEBUG] Initializing attachment handlers for task:', task.id);
  
  // Get attachment elements
  const browseBtn = document.querySelector('.attachment-area .btn-outline-secondary');
  const uploadBtn = document.querySelector('.attachment-area .btn-primary');
  const attachmentArea = document.querySelector('.attachment-area');
  
  if (!browseBtn || !uploadBtn || !attachmentArea) {
    console.warn('[DEBUG] Attachment elements not found in modal');
    return;
  }
  
  // Remove any existing event listeners by cloning elements
  const newBrowseBtn = browseBtn.cloneNode(true);
  const newUploadBtn = uploadBtn.cloneNode(true);
  browseBtn.parentNode.replaceChild(newBrowseBtn, browseBtn);
  uploadBtn.parentNode.replaceChild(newUploadBtn, uploadBtn);
  
  // Create hidden file input
  let fileInput = document.getElementById('attachmentFileInput');
  if (fileInput) {
    fileInput.remove(); // Remove existing to avoid duplicates
  }
  
  fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.id = 'attachmentFileInput';
  fileInput.multiple = true;
  fileInput.style.display = 'none';
  fileInput.accept = '.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.jpg,.jpeg,.png,.gif,.mp4,.mov,.avi';
  document.body.appendChild(fileInput);
  
  let selectedFiles = [];
  
  // Browse button handler
  newBrowseBtn.addEventListener('click', function(e) {
    e.preventDefault();
    console.log('[DEBUG] Browse button clicked');
    fileInput.click();
  });
  
  // File input change handler
  fileInput.addEventListener('change', function(e) {
    const files = Array.from(e.target.files);
    selectedFiles = files;
    console.log('[DEBUG] Files selected:', selectedFiles.length);
    
    // Update UI to show selected files
    if (selectedFiles.length > 0) {
      const fileNames = selectedFiles.map(f => f.name).join(', ');
      const truncatedNames = fileNames.length > 50 ? fileNames.substring(0, 50) + '...' : fileNames;
      
      // Update only the content, keep the same structure
      const statusSpan = attachmentArea.querySelector('.text-muted, .text-success');
      if (statusSpan) {
        statusSpan.className = 'text-muted';
        statusSpan.textContent = `${selectedFiles.length} file(s) selected: ${truncatedNames}`;
      }
      
      // Enable upload button
      const currentUploadBtn = attachmentArea.querySelector('.btn-primary');
      if (currentUploadBtn) {
        currentUploadBtn.disabled = false;
        currentUploadBtn.innerHTML = 'Upload';
      }
    }
  });
  
  // Upload button handler
  newUploadBtn.addEventListener('click', async function(e) {
    e.preventDefault();
    console.log('[DEBUG] Upload button clicked, files:', selectedFiles.length);
    
    if (selectedFiles.length === 0) {
      alert('Please select files to upload.');
      return;
    }
    
    // Disable upload button during upload
    const currentUploadBtn = e.target;
    currentUploadBtn.disabled = true;
    currentUploadBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Uploading...';
    
    let uploadedCount = 0;
    
    try {
      for (const file of selectedFiles) {
        // Validate file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
          alert(`File ${file.name} is too large. Maximum size is 10MB.`);
          continue;
        }
        
        // Upload to CDN
        const formData = new FormData();
        formData.append('file', file);
        
        console.log('[DEBUG] Uploading file to CDN:', file.name);
        const cdnResponse = await fetch('http://localhost:4001/upload', {
          method: 'POST',
          body: formData
        });
        
        if (!cdnResponse.ok) {
          throw new Error(`Failed to upload ${file.name} to CDN`);
        }
        
        const cdnResult = await cdnResponse.json();
        console.log('[DEBUG] CDN upload result:', cdnResult);
        
        // Associate file with task
        const attachmentData = {
          file_name: file.name,
          file_path: cdnResult.url,
          file_size: file.size,
          mime_type: file.type || 'application/octet-stream',
          uploaded_by: window.currentUserId,
          task_id: task.id
        };
        
        console.log('[DEBUG] Creating task attachment:', attachmentData);
        const attachResponse = await fetch(`/api/tasks/${task.id}/attachments`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify(attachmentData)
        });
        
        if (!attachResponse.ok) {
          throw new Error(`Failed to associate ${file.name} with task`);
        }
        
        uploadedCount++;
        console.log('[DEBUG] File successfully attached to task:', file.name);
      }
      
      // Reset form and show success
      selectedFiles = [];
      fileInput.value = '';
      
      // Update UI to show success
      const statusSpan = attachmentArea.querySelector('.text-muted, .text-success');
      if (statusSpan) {
        statusSpan.className = 'text-success';
        statusSpan.textContent = `✓ ${uploadedCount} file(s) uploaded successfully!`;
      }
      
      // Update attachment count badge
      const attachmentBadge = document.querySelector('.task-section .section-header .badge');
      if (attachmentBadge) {
        // Fetch current attachment count
        try {
          const response = await fetch(`/api/tasks/${task.id}/attachments`, {
            credentials: 'include'
          });
          if (response.ok) {
            const attachments = await response.json();
            attachmentBadge.textContent = attachments.length;
          }
        } catch (error) {
          console.warn('Failed to update attachment count:', error);
        }
      }
      
      // Update Files tab if visible
      if (typeof loadProjectFiles === 'function') {
        await loadProjectFiles();
      }
      
    } catch (error) {
      console.error('[DEBUG] Upload error:', error);
      alert('Failed to upload files: ' + error.message);
      
      // Show error in UI
      const statusSpan = attachmentArea.querySelector('.text-muted, .text-success');
      if (statusSpan) {
        statusSpan.className = 'text-danger';
        statusSpan.textContent = 'Upload failed. Please try again.';
      }
    } finally {
      // Re-enable upload button
      currentUploadBtn.disabled = false;
      currentUploadBtn.innerHTML = 'Upload';
    }
  });
  
  // Drag and drop support
  attachmentArea.addEventListener('dragover', function(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    attachmentArea.classList.add('drag-over');
  });
  
  attachmentArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    attachmentArea.classList.remove('drag-over');
  });
  
  attachmentArea.addEventListener('drop', function(e) {
    e.preventDefault();
    attachmentArea.classList.remove('drag-over');
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      selectedFiles = files;
      const fileNames = files.map(f => f.name).join(', ');
      const truncatedNames = fileNames.length > 50 ? fileNames.substring(0, 50) + '...' : fileNames;
      
      const statusSpan = attachmentArea.querySelector('.text-muted, .text-success');
      if (statusSpan) {
        statusSpan.className = 'text-muted';
        statusSpan.textContent = `${files.length} file(s) dropped: ${truncatedNames}`;
      }
      
      const currentUploadBtn = attachmentArea.querySelector('.btn-primary');
      if (currentUploadBtn) {
        currentUploadBtn.disabled = false;
        currentUploadBtn.innerHTML = 'Upload';
      }
    }
  });
  
  console.log('[DEBUG] Attachment handlers initialized successfully');
}

// --- Enhanced Upload Logic: Progress Bar, Loading Spinner, Error State ---
// Patch the upload logic to show progress, loading, and error UI
// Find the upload handler (where uploadBtn is clicked)
// This code assumes the upload button event is set up as in previous code
const originalUploadHandler = async function(task, selectedFiles, fileInput, attachmentArea, currentUploadBtn) {
  let uploadedCount = 0;
  try {
    // Show loading spinner
    let statusSpan = attachmentArea.querySelector('.text-muted, .text-success, .attachment-error');
    if (!statusSpan) {
      statusSpan = document.createElement('span');
      statusSpan.className = 'attachment-loading';
      attachmentArea.appendChild(statusSpan);
    }
    statusSpan.className = 'attachment-loading';
    statusSpan.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';

    for (const file of selectedFiles) {
      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        statusSpan.className = 'attachment-error';
        statusSpan.textContent = `File ${file.name} is too large. Maximum size is 10MB.`;
        continue;
      }

      // Progress bar
      let progressBar = document.createElement('div');
      progressBar.className = 'progress my-2';
      progressBar.innerHTML = '<div class="progress-bar" role="progressbar" style="width: 0%">0%</div>';
      attachmentArea.appendChild(progressBar);

      // Upload to CDN with progress
      const formData = new FormData();
      formData.append('file', file);

      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', 'http://localhost:4001/upload');
        xhr.upload.onprogress = function(e) {
          if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            progressBar.querySelector('.progress-bar').style.width = percent + '%';
            progressBar.querySelector('.progress-bar').textContent = percent + '%';
          }
        };
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            progressBar.querySelector('.progress-bar').classList.add('bg-danger');
            progressBar.querySelector('.progress-bar').textContent = 'Error';
            statusSpan.className = 'attachment-error';
            statusSpan.textContent = `Failed to upload ${file.name} to CDN.`;
            reject(new Error(`Failed to upload ${file.name} to CDN`));
          }
        };
        xhr.onerror = function() {
          progressBar.querySelector('.progress-bar').classList.add('bg-danger');
          progressBar.querySelector('.progress-bar').textContent = 'Error';
          statusSpan.className = 'attachment-error';
          statusSpan.textContent = `Network error uploading ${file.name}.`;
          reject(new Error(`Network error uploading ${file.name}`));
        };
        xhr.send(formData);
      }).then(async (cdnResult) => {
        // Associate file with task
        const attachmentData = {
          file_name: file.name,
          file_path: cdnResult.url,
          file_size: file.size,
          mime_type: file.type || 'application/octet-stream',
          uploaded_by: window.currentUserId,
          task_id: task.id
        };
        const attachResponse = await fetch(`/api/tasks/${task.id}/attachments`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(attachmentData)
        });
        if (!attachResponse.ok) {
          progressBar.querySelector('.progress-bar').classList.add('bg-danger');
          progressBar.querySelector('.progress-bar').textContent = 'Error';
          statusSpan.className = 'attachment-error';
          statusSpan.textContent = `Failed to associate ${file.name} with task.`;
          throw new Error(`Failed to associate ${file.name} with task`);
        }
        progressBar.querySelector('.progress-bar').classList.add('bg-success');
        progressBar.querySelector('.progress-bar').textContent = 'Done';
        uploadedCount++;
      }).catch((err) => {
        // Already handled above
      });
    }

    // Reset form and show success
    selectedFiles = [];
    fileInput.value = '';
    statusSpan.className = 'text-success';
    statusSpan.textContent = `✓ ${uploadedCount} file(s) uploaded successfully!`;

    // Remove progress bars after short delay
    setTimeout(() => {
      attachmentArea.querySelectorAll('.progress').forEach(el => el.remove());
    }, 1000);

    // Update attachment count badge
    const attachmentBadge = document.querySelector('.task-section .section-header .badge');
    if (attachmentBadge) {
      try {
        const response = await fetch(`/api/tasks/${task.id}/attachments`, { credentials: 'include' });
        if (response.ok) {
          const attachments = await response.json();
          attachmentBadge.textContent = attachments.length;
        }
      } catch (error) {
        // Silent fail
      }
    }

    // Update Files tab if visible
    if (typeof loadProjectFiles === 'function') {
      await loadProjectFiles();
    }
  } catch (error) {
    console.error('[DEBUG] Upload error:', error);
    let statusSpan = attachmentArea.querySelector('.text-muted, .text-success, .attachment-error');
    if (!statusSpan) {
      statusSpan = document.createElement('span');
      attachmentArea.appendChild(statusSpan);
    }
    statusSpan.className = 'attachment-error';
    statusSpan.textContent = 'Upload failed: ' + error.message;
  } finally {
    // Re-enable upload button
    if (currentUploadBtn) {
      currentUploadBtn.disabled = false;
      currentUploadBtn.innerHTML = 'Upload';
    }
  }
};
