/* Project Details JavaScript */

document.addEventListener("DOMContentLoaded", function () {
  // Handle Add Task form submission
  const addTaskForm = document.getElementById("addTaskForm");
  if (addTaskForm) {
    addTaskForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(addTaskForm);

      try {
        const response = await fetch(`/projects/${PROJECT_ID}/tasks`, {
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

  // Add delete project functionality
  const deleteProjectBtn = document.getElementById("deleteProjectBtn");
  if (deleteProjectBtn) {
    deleteProjectBtn.addEventListener("click", async function (e) {
      e.preventDefault();

      const projectName = PROJECT_NAME;

      // Confirm deletion
      const confirmMessage = `Are you sure you want to delete the project "${projectName}"? This action cannot be undone.`;

      if (!confirm(confirmMessage)) {
        return;
      }

      try {
        console.log(`Deleting project ${PROJECT_ID}...`);

        const response = await fetch(`/api/projects/${PROJECT_ID}`, {
          method: "DELETE",
          credentials: "include",
        });

        if (response.ok) {
          console.log(`✅ Successfully deleted project ${PROJECT_ID}`);
          alert(`Project "${projectName}" has been deleted successfully!`);

          // Redirect to projects list
          window.location.href = "/projects";
        } else {
          console.error(
            `❌ Failed to delete project ${PROJECT_ID}:`,
            response.status
          );
          alert("Failed to delete the project. Please try again.");
        }
      } catch (error) {
        console.error(`❌ Error deleting project ${PROJECT_ID}:`, error);
        alert(
          "An error occurred while deleting the project. Please try again."
        );
      }
    });
  }
});
