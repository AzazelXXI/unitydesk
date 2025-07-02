// Status Management Functions
let projectStatusData = [];

// Load project statuses when status tab is activated
document.addEventListener('DOMContentLoaded', function() {
  // Load statuses when status tab is clicked
  const statusTab = document.getElementById('statuses-tab');
  if (statusTab) {
    statusTab.addEventListener('shown.bs.tab', function() {
      loadProjectStatuses();
    });
  }
  
  // Setup status creation form
  const createForm = document.getElementById('createCustomStatusForm');
  if (createForm) {
    setupStatusForm();
  }
});

async function loadProjectStatuses() {
  try {
    const response = await fetch(`/api/projects/{{ project.id }}/statuses`);
    const data = await response.json();
    
    if (data.success) {
      projectStatusData = data.data;
      renderProjectStatuses(data.data);
    } else {
      showStatusError('Failed to load project statuses: ' + data.error);
    }
  } catch (error) {
    showStatusError('Error loading statuses: ' + error.message);
  }
}

function renderProjectStatuses(statuses) {
  const container = document.getElementById('projectStatusList');
  if (!container) return;
  
  let html = '';
  
  statuses.forEach(status => {
    const customBadge = status.is_custom ? 
      '<span class="badge bg-info ms-2">Custom</span>' : 
      '<span class="badge bg-light text-dark ms-2">Default</span>';
    
    const finalBadge = status.is_final ? 
      '<span class="badge bg-warning ms-1">Final</span>' : '';
    
    const actions = status.is_custom ? `
    ` : '';
    
    html += `
    `;
  });
  
  if (html === '') {
    html = `
    `;
  }
  
  container.innerHTML = html;
}

function setupStatusForm() {
  // Setup create form
  const colorInput = document.getElementById('customColor');
  const colorPreview = document.getElementById('customColorPreview');
  const statusPreview = document.getElementById('customStatusPreview');
  const statusNameInput = document.getElementById('customStatusName');
  const displayNameInput = document.getElementById('customDisplayName');
  
  function updateCreatePreview() {
    const color = colorInput.value;
    const displayName = displayNameInput.value || statusNameInput.value || 'New Status';
    
    colorPreview.style.backgroundColor = color;
    statusPreview.style.backgroundColor = color;
    statusPreview.textContent = displayName;
  }
  
  colorInput.addEventListener('change', updateCreatePreview);
  statusNameInput.addEventListener('input', function() {
    if (!displayNameInput.value) {/* ... */}
    updateCreatePreview();
  });
  displayNameInput.addEventListener('input', updateCreatePreview);
  
  // Create form submission
  document.getElementById('createCustomStatusForm').addEventListener('submit', async function(e) {
    await createCustomStatus();
  });
  
  // Setup edit form
  const editColorInput = document.getElementById('editColor');
  const editColorPreview = document.getElementById('editColorPreview');
  const editStatusPreview = document.getElementById('editStatusPreview');
  const editDisplayNameInput = document.getElementById('editDisplayName');
  
  function updateEditPreview() {/* ... */}
  
  editColorInput.addEventListener('change', updateEditPreview);
  editDisplayNameInput.addEventListener('input', updateEditPreview);
  
  // Edit form submission
  document.getElementById('editCustomStatusForm').addEventListener('submit', async function(e) {
    await updateCustomStatus();
  });
}

function showCreateStatusModal() {
  const modal = new bootstrap.Modal(document.getElementById('createCustomStatusModal'));
  modal.show();
}

async function createCustomStatus() {
  const form = document.getElementById('createCustomStatusForm');
  const formData = new FormData(form);
  
  try {
  } catch (error) {/* ... */}
}

function showStatusMessage(message, type = 'info') {
  // Create a toast or alert for status messages
}

function showStatusError(message) {/* ... */}

function editStatus(statusId) {/* ... */}

async function updateCustomStatus() {/* ... */}
