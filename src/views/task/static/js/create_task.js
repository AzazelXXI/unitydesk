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
    form.addEventListener("submit", function (event) {
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

      const formData = new FormData(form);
      const data = {};
      formData.forEach((value, key) => (data[key] = value));

      console.log("Form data:", data);
      alert(
        "Task creation form submitted (simulated). Check console for data."
      );
    });
  }
});
