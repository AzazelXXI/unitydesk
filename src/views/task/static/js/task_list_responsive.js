// Enhanced responsive behaviors for task list view

document.addEventListener("DOMContentLoaded", function () {
  // Check viewport size and device capabilities
  const isTouchDevice =
    "ontouchstart" in window || navigator.maxTouchPoints > 0;

  // Setup responsive table actions
  setupResponsiveTableActions();

  // Setup lazy loading for tasks if many exist
  setupLazyLoading();

  // Handle orientation changes on mobile devices
  window.addEventListener("orientationchange", handleOrientationChange);

  /**
   * Sets up alternative actions for table rows on small devices
   */
  function setupResponsiveTableActions() {
    // On very small screens, make the entire row clickable for details
    if (window.innerWidth < 576) {
      const taskRows = document.querySelectorAll("tbody tr");
      taskRows.forEach((row) => {
        // Skip rows that are already clickable
        if (row.querySelector('a[href*="/tasks/"]')) {
          row.style.cursor = "pointer";
          row.addEventListener("click", function (e) {
            // Don't trigger if they clicked a checkbox or button
            if (
              e.target.closest('input[type="checkbox"]') ||
              e.target.closest("button") ||
              e.target.closest("a")
            ) {
              return;
            }

            // Find the task ID
            const taskId = this.cells[1].textContent.trim(); // Assuming title is in the second cell
            // Redirect to task details
            window.location.href = `/tasks/${taskId}`;
          });
        }
      });
    }
  }

  /**
   * Sets up lazy loading for tasks if many exist
   */
  function setupLazyLoading() {
    // Implement if table has many rows
    const taskTable = document.querySelector(".table");
    if (taskTable && taskTable.rows.length > 20) {
      // Could implement virtual scrolling here
      console.log("Many tasks found, would benefit from virtual scrolling");
    }
  }

  /**
   * Handle device orientation changes
   */
  function handleOrientationChange() {
    // Force table to resize properly
    setTimeout(() => {
      const tableResponsive = document.querySelector(".table-responsive");
      if (tableResponsive) {
        tableResponsive.style.width = "99%";
        setTimeout(() => {
          tableResponsive.style.width = "100%";
        }, 50);
      }
    }, 100);
  }
});
