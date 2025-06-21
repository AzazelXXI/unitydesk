document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on a mobile device
  const isMobile = window.innerWidth < 768;

  // Initialize Flatpickr only if elements exist
  const datePickers = document.querySelectorAll(".date-picker");
  if (datePickers.length > 0) {
    flatpickr(".date-picker", {
      dateFormat: "Y-m-d",
      altInput: true,
      altFormat: "F j, Y",
      disableMobile: false, // Better mobile experience
    });
  }
  // Initialize checklist functionality (from new_task.js)
  initializeChecklistFunctionality();

  // Add responsive helper for mobile devices
  if (isMobile) {
    // Improve form readability on mobile
    const formGroups = document.querySelectorAll(".form-group, .mb-3");
    formGroups.forEach((group) => {
      group.classList.add("mb-3");
    });

    // Enhanced mobile form styling (from new_task.js)
    const formInputs = document.querySelectorAll("input, select, textarea");
    formInputs.forEach((input) => {
      if (input.type !== "checkbox" && input.type !== "radio") {
        input.style.padding = "12px";
      }
    });

    // Adjust form layout for mobile
    const formRows = document.querySelectorAll(".form-row");
    formRows.forEach((row) => {
      const columns = row.querySelectorAll(".form-group");
      columns.forEach((col) => {
        col.style.width = "100%";
        col.style.marginRight = "0";
        col.style.marginBottom = "1rem";
      });
    });

    // Make buttons larger for touch
    const buttons = document.querySelectorAll(".button");
    buttons.forEach((button) => {
      button.style.padding = "12px 24px";
    });
  }
  const form = document.getElementById("createTaskForm");
  if (form) {
    form.addEventListener("submit", async function (event) {
      event.preventDefault();

      const taskName = document.getElementById("taskName").value;
      const taskProject = document.getElementById("taskProject").value;

      if (!taskName.trim()) {
        alert("Task Name is required.");
        return;
      }
      if (!taskProject) {
        alert("Project is required.");
        return;
      }

      // Collect form data
      const formData = new FormData(form);
      const taskData = {
        title: formData.get("taskName"),
        name: formData.get("taskName"), // Some APIs expect 'name' instead of 'title'
        description: formData.get("taskDescription") || "",
        project_id: parseInt(formData.get("taskProject")),
        assigned_to_id: formData.get("taskAssignee")
          ? parseInt(formData.get("taskAssignee"))
          : null,
        status: formData.get("taskStatus") || "NOT_STARTED",
        priority: formData.get("taskPriority") || "MEDIUM",
        start_date: formData.get("taskStartDate") || null,
        due_date: formData.get("taskEndDate") || null,
        estimated_hours: formData.get("taskEstimatedTime")
          ? parseInt(formData.get("taskEstimatedTime"))
          : null,
        category: formData.get("taskCategory") || null,
        task_type: formData.get("taskType") || null,
        is_recurring: formData.get("taskIsRecurring") === "on",
      };

      try {
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML =
          '<i class="fas fa-spinner fa-spin me-1"></i> Creating...';
        submitBtn.disabled = true; // Call the API to create the task
        const response = await fetch("/api/simple-tasks/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
          credentials: "same-origin",
          body: JSON.stringify(taskData),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const createdTask = await response.json();

        // Show success message
        if (typeof showToast === "function") {
          showToast("Task created successfully!", "success");
        } else {
          alert("Task created successfully!");
        }

        // Redirect to task list after a short delay
        setTimeout(() => {
          window.location.href = "/tasks";
        }, 1500);
      } catch (error) {
        console.error("Error creating task:", error);

        // Show error message
        if (typeof showToast === "function") {
          showToast(`Failed to create task: ${error.message}`, "danger");
        } else {
          alert(`Failed to create task: ${error.message}`);
        }

        // Reset button
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
      }
    });
  }
});

/**
 * Initialize checklist functionality (merged from new_task.js)
 */
function initializeChecklistFunctionality() {
  const container = document.getElementById("checklist-container");
  const addButton = document.getElementById("add-checklist-item");

  // Add new checklist item
  if (addButton) {
    addButton.addEventListener("click", function () {
      const item = document.createElement("div");
      item.className = "checklist-item";
      item.innerHTML = `
          <input type="text" name="checklist[]" class="checklist-input" placeholder="Checklist item">
          <button type="button" class="remove-item">×</button>
      `;
      container.appendChild(item);

      // Add event listener to the new remove button
      item.querySelector(".remove-item").addEventListener("click", function () {
        container.removeChild(item);
      });

      // Focus the new input field
      item.querySelector("input").focus();
    });
  }

  // Add event listeners to existing remove buttons
  document.querySelectorAll(".remove-item").forEach((button) => {
    button.addEventListener("click", function () {
      const item = this.parentNode;
      container.removeChild(item);
    });
  });
}
