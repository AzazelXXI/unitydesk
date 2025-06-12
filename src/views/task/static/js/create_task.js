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

  // Add responsive helper for mobile devices
  if (isMobile) {
    // Improve form readability on mobile
    const formGroups = document.querySelectorAll(".form-group, .mb-3");
    formGroups.forEach((group) => {
      group.classList.add("mb-3");
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
