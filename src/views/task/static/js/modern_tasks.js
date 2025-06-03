document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on a mobile device
  const isMobile = window.innerWidth < 768;

  // Function to make API requests
  async function apiRequest(url, method = "GET", data = null) {
    try {
      const options = {
        method: method,
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      };

      if (
        data &&
        (method === "POST" || method === "PUT" || method === "PATCH")
      ) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(url, options);

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      // For DELETE requests or others that may not return content
      if (
        response.status === 204 ||
        response.headers.get("Content-Length") === "0"
      ) {
        return true;
      }

      return await response.json();
    } catch (error) {
      console.error("API request error:", error);
      throw error;
    }
  }

  // Initialize date picker for filter (always visible)
  const dueDateFilterElement = document.getElementById("dueDateFilter");
  if (dueDateFilterElement) {
    flatpickr("#dueDateFilter", {
      dateFormat: "Y-m-d",
      allowInput: true,
      wrap: true,
      disableMobile: false, // Better mobile experience
    });
  }
  // Initialize date picker for task modal when modal is shown
  const taskModal = document.getElementById("taskModal");
  if (taskModal) {
    taskModal.addEventListener("shown.bs.modal", function () {
      const taskDueDateElement = document.getElementById("taskDueDate");
      if (taskDueDateElement && !taskDueDateElement._flatpickr) {
        flatpickr("#taskDueDate", {
          dateFormat: "Y-m-d",
          defaultDate: new Date().fp_incr(7), // Default to 7 days from now
          disableMobile: false, // Better mobile experience
        });
      }
    });

    // Improve mobile experience - ensure modal is properly sized
    if (isMobile) {
      taskModal.addEventListener("shown.bs.modal", function () {
        // Auto focus on title field for better UX
        setTimeout(() => {
          const titleField = document.getElementById("taskTitle");
          if (titleField) titleField.focus();
        }, 300);
      });
    }
  }

  // Initialize drag and drop
  const drake = dragula([
    document.getElementById("todo-tasks"),
    document.getElementById("in-progress-tasks"),
    document.getElementById("review-tasks"),
    document.getElementById("done-tasks"),
  ]);

  // Handle drop event to update task status
  drake.on("drop", function (el, target) {
    const taskId = el.getAttribute("data-task-id");
    let newStatus = "";

    switch (target.id) {
      case "todo-tasks":
        newStatus = "todo";
        break;
      case "in-progress-tasks":
        newStatus = "in_progress";
        break;
      case "review-tasks":
        newStatus = "review";
        break;
      case "done-tasks":
        newStatus = "done";
        break;
    }

    if (newStatus) {
      updateTaskStatus(taskId, newStatus);
    }
  });
  // Toggle between board and list views
  const boardView = document.getElementById("boardView");
  const listView = document.getElementById("listView");
  const toggleViewBtn = document.getElementById("toggleView");
  const toggleListViewBtn = document.getElementById("toggleListView");

  toggleViewBtn.addEventListener("click", function () {
    boardView.style.display = "block";
    listView.style.display = "none";
    toggleViewBtn.classList.add("active");
    toggleListViewBtn.classList.remove("active");

    // Store user preference
    localStorage.setItem("taskViewPreference", "board");
  });

  toggleListViewBtn.addEventListener("click", function () {
    boardView.style.display = "none";
    listView.style.display = "block";
    toggleViewBtn.classList.remove("active");
    toggleListViewBtn.classList.add("active");

    // Store user preference
    localStorage.setItem("taskViewPreference", "list");
  });

  // Auto-switch to list view on small screens for better UX
  if (isMobile && !localStorage.getItem("taskViewPreference")) {
    toggleListViewBtn.click();
  } else if (localStorage.getItem("taskViewPreference") === "list") {
    toggleListViewBtn.click();
  }
  // Add touch gestures for mobile
  if (isMobile) {
    // Enable swipe gestures for task cards
    const taskCards = document.querySelectorAll(".task-card");
    let touchStartX = 0;
    let touchEndX = 0;

    taskCards.forEach((card) => {
      card.addEventListener(
        "touchstart",
        (e) => {
          touchStartX = e.changedTouches[0].screenX;
        },
        { passive: true }
      );

      card.addEventListener(
        "touchend",
        (e) => {
          touchEndX = e.changedTouches[0].screenX;
          handleSwipe(card);
        },
        { passive: true }
      );
    });

    function handleSwipe(card) {
      const taskId = card.getAttribute("data-task-id");
      const swipeDistance = touchEndX - touchStartX;

      // If substantial swipe right, quickly view task details
      if (swipeDistance > 70) {
        showTaskDetails(taskId);
      }
    } // Add filter toggle functionality for small screens
    const filterRow = document.querySelector(".task-filter-row");
    if (filterRow) {
      // Create an explicit toggle button with better semantics and accessibility
      const filterToggle = document.createElement("button");
      filterToggle.className = "filter-toggle-btn d-md-none"; // Only show on mobile
      filterToggle.setAttribute("type", "button");
      filterToggle.setAttribute("aria-expanded", "false");
      filterToggle.setAttribute("aria-controls", "task-filters");
      filterToggle.innerHTML =
        '<i class="fas fa-filter me-2"></i>Filters <i class="fas fa-chevron-down ms-1"></i>';

      // Insert toggle before filter row
      filterRow.parentNode.insertBefore(filterToggle, filterRow);

      // Add id to the filter row for aria-controls
      filterRow.id = "task-filters";

      // Function to check screen size and update filter visibility
      function updateFilterVisibility() {
        // Temporarily disable transitions during resize
        filterRow.classList.add("no-transition");

        if (window.innerWidth <= 576) {
          // XS screens - collapsed by default
          if (!filterToggle.classList.contains("expanded")) {
            filterRow.classList.remove("expanded");
          }
        } else if (window.innerWidth < 768) {
          // SM screens - expanded by default
          filterRow.classList.add("expanded");
          filterToggle.classList.add("expanded");
          filterToggle.setAttribute("aria-expanded", "true");
          const icon = filterToggle.querySelector(
            ".fa-chevron-down, .fa-chevron-up"
          );
          if (icon) {
            icon.className = "fas fa-chevron-up ms-1";
          }
        }

        // Force reflow to apply changes immediately
        void filterRow.offsetWidth;

        // Re-enable transitions after a short delay
        setTimeout(() => {
          filterRow.classList.remove("no-transition");
        }, 50);
      }

      // Create debounced resize function for better performance
      let resizeTimeout;
      function debouncedResize() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(updateFilterVisibility, 100);
      }

      // Initial check
      updateFilterVisibility();

      // Add resize listener with debounce
      window.addEventListener("resize", debouncedResize);

      // Add click event to the toggle button
      filterToggle.addEventListener("click", function () {
        const isExpanded = filterRow.classList.toggle("expanded");

        // Update button state
        this.classList.toggle("expanded", isExpanded);
        this.setAttribute("aria-expanded", isExpanded ? "true" : "false");

        // Update the icon based on state
        const icon = this.querySelector(".fa-chevron-down, .fa-chevron-up");
        icon.className = isExpanded
          ? "fas fa-chevron-up ms-1"
          : "fas fa-chevron-down ms-1";

        // Ensure the filter row is visible when expanded (scroll to it if needed)
        if (isExpanded) {
          setTimeout(() => {
            filterRow.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }, 100);
        }
      });

      // Remove the direct click handler on filterRow as we now have a proper button
      // but keep the row itself clickable only in the header area for larger tap targets
      const filterHeader = document.createElement("div");
      filterHeader.className = "d-md-none filter-header";
      filterHeader.innerHTML = "<div>Filters</div>";

      // Handle outside clicks to close filter panel
      document.addEventListener("click", function (e) {
        if (
          filterRow.classList.contains("expanded") &&
          !filterRow.contains(e.target) &&
          e.target !== filterToggle &&
          !filterToggle.contains(e.target)
        ) {
          filterRow.classList.remove("expanded");
          filterToggle.classList.remove("expanded");
          filterToggle.setAttribute("aria-expanded", "false");

          const icon = filterToggle.querySelector(
            ".fa-chevron-down, .fa-chevron-up"
          );
          if (icon) {
            icon.className = "fas fa-chevron-down ms-1";
          }
        }
      });

      // Automatically expand filters if any filter is applied
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.toString()) {
        filterRow.classList.add("expanded");
        filterToggle.classList.add("expanded");
        filterToggle.setAttribute("aria-expanded", "true");

        const icon = filterToggle.querySelector(".fa-chevron-down");
        if (icon) {
          icon.className = "fas fa-chevron-up ms-1";
        }
      }
    }
  }

  // Initialize task modals
  const taskModalInstance = new bootstrap.Modal(
    document.getElementById("taskModal")
  );
  const taskDetailsModal = new bootstrap.Modal(
    document.getElementById("taskDetailsModal")
  );
  const newTaskBtn = document.getElementById("newTaskBtn");
  const saveTaskBtn = document.getElementById("saveTaskBtn");

  newTaskBtn.addEventListener("click", function () {
    document.getElementById("taskForm").reset();
    document.getElementById("taskId").value = "";
    document.getElementById("taskModalLabel").textContent = "New Task";
    taskModalInstance.show();
  });

  saveTaskBtn.addEventListener("click", function () {
    if (validateForm(document.getElementById("taskForm"))) {
      saveTask();
    }
  });

  // Task card click to show details
  document.querySelectorAll(".task-card").forEach((card) => {
    card.addEventListener("click", function () {
      const taskId = this.getAttribute("data-task-id");
      showTaskDetails(taskId);
    });
  });

  // Table view action buttons
  document.querySelectorAll(".btn-view").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const taskId = this.getAttribute("data-task-id");
      showTaskDetails(taskId);
    });
  });

  document.querySelectorAll(".btn-edit").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const taskId = this.getAttribute("data-task-id");
      editTask(taskId);
    });
  });

  document.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const taskId = this.getAttribute("data-task-id");
      confirmDeleteTask(taskId);
    });
  });

  // Task details modal actions
  document
    .getElementById("editTaskFromDetails")
    .addEventListener("click", function () {
      const taskId = this.getAttribute("data-task-id");
      taskDetailsModal.hide();
      editTask(taskId);
    });

  document
    .getElementById("deleteTaskFromDetails")
    .addEventListener("click", function () {
      const taskId = this.getAttribute("data-task-id");
      taskDetailsModal.hide();
      confirmDeleteTask(taskId);
    });
  // Filter events
  document
    .getElementById("projectFilter")
    .addEventListener("change", applyFilters);
  document
    .getElementById("assigneeFilter")
    .addEventListener("change", applyFilters);
  document
    .getElementById("priorityFilter")
    .addEventListener("change", applyFilters);
  document.getElementById("searchBtn").addEventListener("click", applyFilters);

  if (dueDateFilterElement) {
    dueDateFilterElement.addEventListener("change", applyFilters);
  }

  // Search on Enter key
  document
    .getElementById("searchInput")
    .addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        applyFilters();
      }
    });

  // Comment input
  document
    .getElementById("addCommentBtn")
    .addEventListener("click", function () {
      const commentInput = document.getElementById("commentInput");
      const taskId = document
        .getElementById("editTaskFromDetails")
        .getAttribute("data-task-id");

      if (commentInput.value.trim() !== "") {
        addComment(taskId, commentInput.value);
        commentInput.value = "";
      }
    });

  // Functions
  function updateTaskStatus(taskId, status) {
    // Call API to update task status
    apiRequest(`/api/v1/tasks/${taskId}/status`, "PATCH", { status })
      .then((response) => {
        showToast(
          `Task status updated to ${status.replace("_", " ")}`,
          "success"
        );
      })
      .catch((error) => {
        console.error("Error updating task status:", error);
        showToast("Failed to update task status", "danger");
      });
  }

  function showTaskDetails(taskId) {
    // Dữ liệu mock tạm thời
    const mockTask = {
      id: taskId,
      title: "Thiết kế giao diện dashboard",
      description:
        "Thiết kế giao diện dashboard cho dự án quản lý công việc. Bao gồm các widget thống kê, biểu đồ tiến độ và danh sách task.",
      status: "in_progress",
      priority: "high",
      due_date: "2025-06-10",
      created_at: "2025-05-20",
      project: { name: "CSA Platform" },
      assignee: { name: "Nguyễn Văn A", initials: "NA" },
    };

    // Fill in task details
    document.getElementById("detailsTitle").textContent = mockTask.title;
    document.getElementById("detailsDescription").textContent =
      mockTask.description;

    // Update status badge
    const statusBadge = document.getElementById("detailsStatus");
    statusBadge.textContent = mockTask.status
      .replace("_", " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
    statusBadge.className = "badge float-end";
    if (mockTask.status === "todo") statusBadge.classList.add("bg-secondary");
    else if (mockTask.status === "in_progress")
      statusBadge.classList.add("bg-primary");
    else if (mockTask.status === "review")
      statusBadge.classList.add("bg-warning");
    else if (mockTask.status === "done")
      statusBadge.classList.add("bg-success");

    // Update priority badge
    const priorityBadge = document.getElementById("detailsPriority");
    priorityBadge.textContent =
      mockTask.priority.charAt(0).toUpperCase() + mockTask.priority.slice(1);
    priorityBadge.className = "badge float-end";
    if (mockTask.priority === "high") priorityBadge.classList.add("bg-danger");
    else if (mockTask.priority === "medium")
      priorityBadge.classList.add("bg-warning");
    else if (mockTask.priority === "low")
      priorityBadge.classList.add("bg-success");

    // Fill other details
    document.getElementById("detailsDueDate").textContent = formatDate(
      mockTask.due_date
    );
    document.getElementById("detailsCreated").textContent = formatDate(
      mockTask.created_at
    );
    document.getElementById("detailsProject").textContent =
      mockTask.project.name;
    document.getElementById("detailsAssignee").textContent =
      mockTask.assignee.name;
    document.getElementById("detailsAssigneeAvatar").textContent =
      mockTask.assignee.initials;

    // Set task ID for action buttons
    document
      .getElementById("editTaskFromDetails")
      .setAttribute("data-task-id", mockTask.id);
    document
      .getElementById("deleteTaskFromDetails")
      .setAttribute("data-task-id", mockTask.id);

    // Xóa comment cũ và hiển thị comment mẫu
    const commentsContainer = document.getElementById("comments");
    commentsContainer.innerHTML = `<div class='d-flex mb-3'>
      <div class='assignee-avatar me-2' title='Nguyễn Văn A'>NA</div>
      <div class='flex-grow-1'>
        <div class='d-flex justify-content-between'>
          <h6 class='mb-0'>Nguyễn Văn A</h6>
          <small class='text-muted'>2025-06-01 09:00</small>
        </div>
        <div>Đã hoàn thành phần layout chính.</div>
      </div>
    </div>`;

    // Show modal
    taskDetailsModal.show();
  }

  function editTask(taskId) {
    // Call API to get task for editing
    apiRequest(`/api/v1/tasks/${taskId}`, "GET")
      .then((task) => {
        // Fill the form with task data
        document.getElementById("taskId").value = task.id;
        document.getElementById("taskTitle").value = task.title;
        document.getElementById("taskDescription").value = task.description;
        document.getElementById("taskStatus").value = task.status;
        document.getElementById("taskProject").value = task.project.id;
        document.getElementById("taskAssignee").value = task.assignee.id;
        document.getElementById("taskDueDate").value = task.due_date;
        document.getElementById("taskPriority").value = task.priority;

        // Update modal title and show
        document.getElementById("taskModalLabel").textContent = "Edit Task";
        taskModalInstance.show();
      })
      .catch((error) => {
        console.error("Error fetching task for editing:", error);
        showToast("Failed to load task data", "danger");
      });
  }

  function saveTask() {
    const taskId = document.getElementById("taskId").value;

    const taskData = {
      title: document.getElementById("taskTitle").value,
      description: document.getElementById("taskDescription").value,
      status: document.getElementById("taskStatus").value,
      project_id: document.getElementById("taskProject").value,
      assignee_id: document.getElementById("taskAssignee").value,
      due_date: document.getElementById("taskDueDate").value,
      priority: document.getElementById("taskPriority").value,
    };

    // Determine if this is an create or update
    const method = taskId ? "PUT" : "POST";
    const url = taskId ? `/api/v1/tasks/${taskId}` : "/api/v1/tasks";

    apiRequest(url, method, taskData)
      .then((response) => {
        taskModalInstance.hide();
        showToast(
          taskId ? "Task updated successfully" : "Task created successfully",
          "success"
        );
        // Reload page to show changes
        setTimeout(() => window.location.reload(), 1000);
      })
      .catch((error) => {
        console.error("Error saving task:", error);
        showToast("Failed to save task", "danger");
      });
  }

  function confirmDeleteTask(taskId) {
    confirmDialog("Are you sure you want to delete this task?", () => {
      deleteTask(taskId);
    });
  }

  function deleteTask(taskId) {
    apiRequest(`/api/v1/tasks/${taskId}`, "DELETE")
      .then((response) => {
        showToast("Task deleted successfully", "success");
        // Reload page to show changes
        setTimeout(() => window.location.reload(), 1000);
      })
      .catch((error) => {
        console.error("Error deleting task:", error);
        showToast("Failed to delete task", "danger");
      });
  }

  function loadComments(taskId) {
    // Call API to get task comments
    apiRequest(`/api/v1/tasks/${taskId}/comments`, "GET")
      .then((comments) => {
        const commentsContainer = document.getElementById("comments");
        commentsContainer.innerHTML = "";

        if (comments.length === 0) {
          commentsContainer.innerHTML =
            '<p class="text-center text-muted">No comments yet</p>';
          return;
        }

        comments.forEach((comment) => {
          const commentHTML = `
            <div class="d-flex mb-3">
                <div class="assignee-avatar me-2" title="${comment.user.name}">
                    ${comment.user.initials}
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between">
                        <h6 class="mb-0">${comment.user.name}</h6>
                        <small class="text-muted">${formatDateTime(
                          comment.created_at
                        )}</small>
                    </div>
                    <div>${comment.content}</div>
                </div>
            </div>
          `;

          commentsContainer.innerHTML += commentHTML;
        });
      })
      .catch((error) => {
        console.error("Error loading comments:", error);
        document.getElementById("comments").innerHTML =
          '<p class="text-center text-danger">Failed to load comments</p>';
      });
  }

  function addComment(taskId, content) {
    apiRequest(`/api/v1/tasks/${taskId}/comments`, "POST", { content })
      .then((response) => {
        showToast("Comment added", "success");
        loadComments(taskId);
      })
      .catch((error) => {
        console.error("Error adding comment:", error);
        showToast("Failed to add comment", "danger");
      });
  }

  function applyFilters() {
    const project = document.getElementById("projectFilter").value;
    const assignee = document.getElementById("assigneeFilter").value;
    const priority = document.getElementById("priorityFilter").value;
    const dueDateElement = document.getElementById("dueDateFilter");
    const dueDate = dueDateElement ? dueDateElement.value : "";
    const searchText = document.getElementById("searchInput").value;

    // Build query string
    const params = new URLSearchParams();
    if (project) params.append("project_id", project);
    if (assignee) params.append("assignee_id", assignee);
    if (priority) params.append("priority", priority);
    if (dueDate) params.append("due_date", dueDate);
    if (searchText) params.append("search", searchText);

    // Redirect with filters
    window.location.href = `/tasks?${params.toString()}`;
  }

  // Utility function to format dates
  function formatDate(dateString) {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  // Utility function to format date with time
  function formatDateTime(dateTimeString) {
    if (!dateTimeString) return "N/A";
    const date = new Date(dateTimeString);
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // Utility function to show toast messages
  function showToast(message, type = "info") {
    // Check if toast container exists, if not create one
    let toastContainer = document.getElementById("toast-container");
    if (!toastContainer) {
      toastContainer = document.createElement("div");
      toastContainer.id = "toast-container";
      toastContainer.className =
        "toast-container position-fixed bottom-0 end-0 p-3";
      document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = `toast-${Date.now()}`;
    const toast = document.createElement("div");
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type}`;
    toast.setAttribute("role", "alert");
    toast.setAttribute("aria-live", "assertive");
    toast.setAttribute("aria-atomic", "true");

    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

    toastContainer.appendChild(toast);

    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 5000 });
    bsToast.show();

    // Remove the toast after it's hidden
    toast.addEventListener("hidden.bs.toast", function () {
      toast.remove();
    });
  }

  // Utility function for confirmation dialogs
  function confirmDialog(message, callback) {
    if (confirm(message)) {
      callback();
    }
  }
});
