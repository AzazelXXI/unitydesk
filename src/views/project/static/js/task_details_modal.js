// Setup Delete Task button logic
document.addEventListener('DOMContentLoaded', function() {
  var deleteBtn = document.getElementById('deleteTaskBtn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', function() {
      var taskId = deleteBtn.getAttribute('data-task-id');
      if (!taskId) {
        alert('Task ID not found.');
        return;
      }
      if (!confirm('Are you sure you want to delete this task? This action cannot be undone.')) {
        return;
      }
      fetch('/api/tasks/' + taskId, {
        method: 'DELETE',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/json',
        },
      })
      .then(function(response) {
        if (response.ok) {
          // Hide the modal
          var modal = document.getElementById('taskDetailsModal');
          if (modal) {
            var modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
              modalInstance.hide();
            }
          }
          // Optionally refresh the page or update the UI
          location.reload();
        } else {
          return response.json().then(function(data) {
            throw new Error(data.message || 'Failed to delete task.');
          });
        }
      })
      .catch(function(error) {
        alert('Error: ' + error.message);
      });
    });
  }
});
// Expose setCloneTaskFormAction globally for project_details.js compatibility
window.setCloneTaskFormAction = setCloneTaskFormAction;

function setCloneTaskFormAction(taskId) {
  var form = document.getElementById('cloneTaskForm');
  if (form && taskId) {
    form.action = '/tasks/' + taskId + '/clone';
    // Also set the task id on the delete button for consistency
    var deleteBtn = document.getElementById('deleteTaskBtn');
    if (deleteBtn) {
      deleteBtn.setAttribute('data-task-id', taskId);
    }
  }
}

// Inline editing for task status and priority in the task details modal
// This script is loaded only when the modal is present and has the required context

// Inline editing for task status and priority in the task details modal
// This script is loaded only when the modal is present and has the required context
document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('taskDetailsModal');
  if (!modal) return;

  // Listen for modal show event to setup inline editing
  modal.addEventListener('show.bs.modal', function(event) {
    // Try to get taskId and context from the modal or event
    setTimeout(() => {
      const taskId = modal.getAttribute('data-task-id');
      if (!taskId) return;
      fetch(`/api/tasks/${taskId}`)
        .then(res => res.json())
        .then(data => {
          if (data.success && data.task) {
            showInlineEditFields(data.task);
          }
        });
    }, 100);
  });

  // If modal is already open (e.g. on page load), setup immediately
  if (modal.classList.contains('show')) {
    const taskId = modal.getAttribute('data-task-id');
    if (taskId) {
      fetch(`/api/tasks/${taskId}`)
        .then(res => res.json())
        .then(data => {
          if (data.success && data.task) {
            showInlineEditFields(data.task);
          }
        });
    }
  }
});

function showInlineEditFields(task) {
  // Show the inline edit fields and populate dropdowns
  const fieldsDiv = document.getElementById('taskInlineEditFields');
  if (fieldsDiv) fieldsDiv.style.display = '';

  // Populate status dropdown
  const statusDropdown = document.getElementById('taskStatusDropdown');
  if (statusDropdown && task.status_options) {
    statusDropdown.innerHTML = '';
    task.status_options.forEach(opt => {
      const option = document.createElement('option');
      option.value = opt.value;
      option.textContent = opt.label;
      if (opt.value === task.status) option.selected = true;
      statusDropdown.appendChild(option);
    });
    statusDropdown.addEventListener('change', function() {
      updateTaskField(task.id, 'status', statusDropdown.value);
    });
  }

  // Populate priority dropdown
  const priorityDropdown = document.getElementById('taskPriorityDropdown');
  if (priorityDropdown) {
    priorityDropdown.value = task.priority || 'MEDIUM';
    priorityDropdown.addEventListener('change', function() {
      updateTaskField(task.id, 'priority', priorityDropdown.value);
    });
  }

  // ...existing code...
}

function updateTaskField(taskId, field, value) {
  if (!taskId) return;
  fetch(`/api/tasks/${taskId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: JSON.stringify({ [field]: value })
  })
  .then(response => response.json())
  .then(data => {
    if (!data.success) {
      showTaskEditError(`Failed to update ${field}: ${data.error || 'Unknown error'}`);
    }
  })
  .catch(err => {
    showTaskEditError(`Error updating ${field}: ${err.message}`);
  });
}

function showTaskEditError(message) {
  // Show a toast or alert in the modal
  const alert = document.createElement('div');
  alert.className = 'alert alert-danger';
  alert.textContent = message;
  const modalBody = document.querySelector('#taskDetailsModal .modal-body');
  if (modalBody) {
    modalBody.prepend(alert);
    setTimeout(() => alert.remove(), 4000);
  }
}
