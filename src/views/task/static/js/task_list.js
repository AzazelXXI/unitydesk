document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on a mobile device
  const isMobile = isMobileDevice();
  // Check if we're on a small screen (regardless of device type)
  const isSmallScreen = window.innerWidth < 768;

  // Task checkboxes
  document
    .querySelectorAll('input[type="checkbox"]')
    .forEach(function (checkbox) {
      checkbox.addEventListener("change", function () {
        const row = this.closest("tr");
        if (this.checked) {
          row.style.opacity = "0.6";
        } else {
          row.style.opacity = "1";
        }
      });
    });

  // Helper function to adjust layout based on screen size
  function adjustLayout() {
    const isNowSmallScreen = window.innerWidth < 768;

    // Handle responsive table
    const table = document.querySelector(".table");
    if (table) {
      // Always make sure table is responsive
      if (!table.parentElement.classList.contains("table-responsive")) {
        const wrapper = document.createElement("div");
        wrapper.className = "table-responsive";
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      }

      // Hide/show columns based on screen size
      const projectCol = document.querySelectorAll(
        "th:nth-child(3), td:nth-child(3)"
      );
      const dueDateCol = document.querySelectorAll(
        "th:nth-child(6), td:nth-child(6)"
      );

      if (isNowSmallScreen) {
        projectCol.forEach((cell) => cell.classList.add("mobile-hide"));
        dueDateCol.forEach((cell) => cell.classList.add("mobile-hide"));
      } else {
        projectCol.forEach((cell) => cell.classList.remove("mobile-hide"));
        dueDateCol.forEach((cell) => cell.classList.remove("mobile-hide"));
      }
    }
  }

  // Mobile-specific enhancements
  if (isMobile || isSmallScreen) {
    // Create filter toggle for small screens
    const filterSection = document.querySelector(".task-filter-section");
    if (filterSection) {
      const filterRow = document.querySelector(".row.g-3");
      if (filterRow) {
        filterRow.classList.add("task-filter-row");

        // Create toggle button
        const toggleButton = document.createElement("div");
        toggleButton.className = "task-filter-toggle";
        toggleButton.innerHTML = 'Filters <i class="fas fa-chevron-down"></i>';

        // Insert toggle before the filter row
        filterSection.insertBefore(toggleButton, filterRow);

        // Add click handler for toggle
        toggleButton.addEventListener("click", function () {
          filterRow.classList.toggle("expanded");
          const icon = this.querySelector("i");
          if (filterRow.classList.contains("expanded")) {
            icon.className = "fas fa-chevron-up";
          } else {
            icon.className = "fas fa-chevron-down";
          }
        });
      }
    }

    // Run initial layout adjustment
    adjustLayout();
  }

  // Listen for window resize events to adjust responsive behavior
  window.addEventListener("resize", adjustLayout);
});
