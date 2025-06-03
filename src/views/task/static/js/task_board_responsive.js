/**
 * Responsive behavior management for task board
 */
document.addEventListener("DOMContentLoaded", function () {
  const taskBoard = document.querySelector(".task-board");

  // Don't proceed if no task board is found
  if (!taskBoard) return;

  // Setup action hints for column headers
  setupColumnActionHints();

  // Add visual indicator for scrolling if needed
  addScrollIndicators();

  // Add responsive handling for columns
  initResponsiveColumns();

  // Add swipe behavior for mobile
  enhanceSwipeGestures();

  // Handle column visibility toggle for small screens
  setupColumnToggle();

  /**
   * Setup column header data attributes for expand/collapse
   */
  function setupColumnActionHints() {
    const columnHeaders = document.querySelectorAll(".task-column-header");

    columnHeaders.forEach((header) => {
      // Set initial state
      header.setAttribute("data-action", "collapse");

      // Update the action hint when column state changes
      const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
          if (
            mutation.type === "attributes" &&
            mutation.attributeName === "class"
          ) {
            const column = header.closest(".task-column");
            if (column.classList.contains("collapsed")) {
              header.setAttribute("data-action", "expand");
            } else {
              header.setAttribute("data-action", "collapse");
            }
          }
        });
      });

      // Start observing the column for class changes
      observer.observe(header.closest(".task-column"), {
        attributes: true,
      });

      // Add visual indicator for expand/collapse
      const actionIndicator = document.createElement("span");
      actionIndicator.className = "column-action-indicator";
      actionIndicator.innerHTML = '<i class="fas fa-chevron-up"></i>';
      header.appendChild(actionIndicator);
    });
  }

  /**
   * Add visual indicators for horizontal scrolling
   */
  function addScrollIndicators() {
    // Remove any existing indicators first to prevent duplicates
    document
      .querySelectorAll(".task-board-scroll-indicator")
      .forEach((el) => el.remove());

    // Check if scrolling is needed and if we're not in stacked layout
    if (
      taskBoard.scrollWidth > taskBoard.clientWidth &&
      window.innerWidth >= 768
    ) {
      // Create indicator elements
      const leftIndicator = document.createElement("div");
      leftIndicator.className = "task-board-scroll-indicator left";
      leftIndicator.setAttribute("aria-label", "Scroll left");
      leftIndicator.setAttribute("role", "button");
      leftIndicator.setAttribute("tabindex", "0");
      leftIndicator.innerHTML = '<i class="fas fa-chevron-left"></i>';

      const rightIndicator = document.createElement("div");
      rightIndicator.className = "task-board-scroll-indicator right";
      rightIndicator.setAttribute("aria-label", "Scroll right");
      rightIndicator.setAttribute("role", "button");
      rightIndicator.setAttribute("tabindex", "0");
      rightIndicator.innerHTML = '<i class="fas fa-chevron-right"></i>';

      // Insert indicators
      taskBoard.parentNode.insertBefore(leftIndicator, taskBoard);
      taskBoard.parentNode.appendChild(rightIndicator);

      // Initially hide left indicator if scrolled all the way left
      if (taskBoard.scrollLeft <= 10) {
        leftIndicator.style.opacity = "0.3";
        leftIndicator.style.pointerEvents = "none";
      }

      // Handle scroll events to update indicator states
      taskBoard.addEventListener("scroll", () => {
        // If scrolled all the way left, dim the left indicator
        if (taskBoard.scrollLeft <= 10) {
          leftIndicator.style.opacity = "0.3";
          leftIndicator.style.pointerEvents = "none";
        } else {
          leftIndicator.style.opacity = "1";
          leftIndicator.style.pointerEvents = "auto";
        }

        // If scrolled all the way right, dim the right indicator
        if (
          Math.abs(
            taskBoard.scrollWidth - taskBoard.clientWidth - taskBoard.scrollLeft
          ) <= 10
        ) {
          rightIndicator.style.opacity = "0.3";
          rightIndicator.style.pointerEvents = "none";
        } else {
          rightIndicator.style.opacity = "1";
          rightIndicator.style.pointerEvents = "auto";
        }
      });

      // Add behavior with improved scrolling
      leftIndicator.addEventListener("click", () => {
        // Scroll one column width to the left
        const columnWidth =
          document.querySelector(".task-column")?.offsetWidth || 200;
        const scrollAmount = Math.min(columnWidth + 15, taskBoard.scrollLeft);
        taskBoard.scrollBy({ left: -scrollAmount, behavior: "smooth" });
      });

      rightIndicator.addEventListener("click", () => {
        // Scroll one column width to the right
        const columnWidth =
          document.querySelector(".task-column")?.offsetWidth || 200;
        taskBoard.scrollBy({ left: columnWidth + 15, behavior: "smooth" });
      });

      // Keyboard accessibility
      leftIndicator.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          leftIndicator.click();
        }
      });

      rightIndicator.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          rightIndicator.click();
        }
      });

      // Add touch/swipe support for indicators with better visual feedback
      leftIndicator.addEventListener(
        "touchstart",
        function () {
          this.style.backgroundColor = "#f0f0f0";
          this.style.transform = "scale(0.95)";
        },
        { passive: true }
      );

      leftIndicator.addEventListener(
        "touchend",
        function () {
          this.style.backgroundColor = "rgba(255, 255, 255, 0.9)";
          this.style.transform = "scale(1)";
        },
        { passive: true }
      );

      rightIndicator.addEventListener("touchstart", function () {
        this.style.backgroundColor = "#f0f0f0";
      });

      rightIndicator.addEventListener("touchend", function () {
        this.style.backgroundColor = "rgba(255, 255, 255, 0.9)";
      });

      // Show/hide indicators based on scroll position
      taskBoard.addEventListener("scroll", updateIndicators);
      window.addEventListener("resize", updateIndicators); // Update on resize too
      updateIndicators();
    }
  }

  function updateIndicators() {
    const leftIndicator = document.querySelector(
      ".task-board-scroll-indicator.left"
    );
    const rightIndicator = document.querySelector(
      ".task-board-scroll-indicator.right"
    );

    if (leftIndicator && rightIndicator) {
      // Show left indicator if not at start
      leftIndicator.style.opacity = taskBoard.scrollLeft > 10 ? "1" : "0";

      // Show right indicator if not at end
      const isAtEnd =
        taskBoard.scrollLeft + taskBoard.clientWidth >=
        taskBoard.scrollWidth - 10;
      rightIndicator.style.opacity = isAtEnd ? "0" : "1";
    }
  }

  /**
   * Setup columns to be more responsive
   */
  function initResponsiveColumns() {
    const columns = document.querySelectorAll(".task-column");

    // Make columns tabbable for accessibility
    columns.forEach((column) => {
      column.setAttribute("tabindex", "0");

      // Focus on column when clicked (for keyboard navigation)
      column.addEventListener("click", function (e) {
        // Don't focus if clicking the header in mobile view (for collapse/expand)
        const isClickOnHeader = e.target.closest(".task-column-header");
        const isMobile = window.innerWidth < 768;

        if (!(isClickOnHeader && isMobile)) {
          this.focus();
        }
      });

      // Setup collapsible behavior for mobile
      const header = column.querySelector(".task-column-header");
      if (header) {
        header.addEventListener("click", function () {
          // Only enable collapse/expand on mobile
          if (window.innerWidth < 768) {
            const parentColumn = this.closest(".task-column");
            toggleColumnCollapse(parentColumn);
          }
        });
      }
    });

    // Adjust task columns on window resize
    window.addEventListener("resize", adjustColumnSizes);

    // Initial adjustment
    adjustColumnSizes();

    function adjustColumnSizes() {
      const isMobile = window.innerWidth < 768;
      const isSmall = window.innerWidth < 576;

      if (isMobile) {
        // Apply stacked layout styles
        taskBoard.classList.add("stacked-layout");

        // Update column action indicators
        document
          .querySelectorAll(".column-action-indicator")
          .forEach((indicator) => {
            indicator.style.display = "block";
          });

        // For stacked layout, expand only the In Progress column by default
        columns.forEach((column) => {
          if (!column.classList.contains("column-in-progress")) {
            column.classList.add("collapsed");
          }

          // Make column tasks have a fixed max-height for better UX
          const tasksContainer = column.querySelector(".task-column-tasks");
          if (tasksContainer) {
            tasksContainer.style.maxHeight = "300px";
          }
        });

        // Make sure In Progress column is visible
        const inProgressColumn = document.querySelector(".column-in-progress");
        if (inProgressColumn) {
          inProgressColumn.classList.remove("collapsed");
          // Scroll to this column
          setTimeout(() => {
            inProgressColumn.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          }, 300);
        }
      } else {
        // Remove stacked layout styles
        taskBoard.classList.remove("stacked-layout");

        // Hide column action indicators in horizontal layout
        document
          .querySelectorAll(".column-action-indicator")
          .forEach((indicator) => {
            indicator.style.display = "none";
          });

        // For horizontal layout, make sure all columns are expanded
        columns.forEach((column) => {
          column.classList.remove("collapsed");

          // Reset column tasks height for horizontal layout
          const tasksContainer = column.querySelector(".task-column-tasks");
          if (tasksContainer) {
            tasksContainer.style.maxHeight = "";
          }
        });

        // In horizontal layout, scroll to In Progress
        if (isSmall) {
          scrollToActiveColumn();
        }
      }
    }

    // Helper to scroll to column with active tasks (e.g., in-progress)
    function scrollToActiveColumn() {
      // Find the "In Progress" column as that's typically most important
      const inProgressColumn = document.querySelector(".column-in-progress");
      if (inProgressColumn) {
        // Smooth scroll to show this column
        setTimeout(() => {
          taskBoard.scrollTo({
            left: inProgressColumn.offsetLeft - 10,
            behavior: "smooth",
          });
        }, 300);
      }
    }

    // Toggle column collapse state
    function toggleColumnCollapse(column) {
      if (column.classList.contains("collapsed")) {
        // Expand this column
        column.classList.remove("collapsed");

        // Only in stacked layout (mobile), we want to collapse other columns when expanding one
        if (window.innerWidth < 768) {
          const allColumns = document.querySelectorAll(".task-column");
          allColumns.forEach((otherColumn) => {
            if (otherColumn !== column) {
              otherColumn.classList.add("collapsed");
            }
          });

          // Scroll to the expanded column
          setTimeout(() => {
            column.scrollIntoView({ behavior: "smooth", block: "start" });
          }, 100);
        }
      } else {
        // Collapse this column
        column.classList.add("collapsed");
      }
    }
  }

  /**
   * Enhance swipe gestures for mobile
   */
  function enhanceSwipeGestures() {
    // Check if we're on a mobile device via touch capability
    if (!("ontouchstart" in window)) return;

    let startX, startScrollX;
    let isSwiping = false;

    taskBoard.addEventListener(
      "touchstart",
      function (e) {
        startX = e.touches[0].pageX;
        startScrollX = this.scrollLeft;
        isSwiping = true;
      },
      { passive: true }
    );

    taskBoard.addEventListener(
      "touchmove",
      function (e) {
        if (!isSwiping) return;

        const x = e.touches[0].pageX;
        const walk = (startX - x) * 1.5; // Faster scroll
        this.scrollLeft = startScrollX + walk;
      },
      { passive: true }
    );

    taskBoard.addEventListener(
      "touchend",
      function () {
        isSwiping = false;
      },
      { passive: true }
    );
  }

  /**
   * Setup column toggle for mobile screens
   */
  function setupColumnToggle() {
    // Add a column selector for mobile screens
    // We'll place it at the bottom of the viewport for easier thumb access
    const taskBoardContainer = document.querySelector(".task-board-container");

    // Only proceed if we found the container
    if (!taskBoardContainer) return;

    // Remove any existing selector (in case of resize/reload)
    const existingSelector = document.querySelector(".column-pill-nav");
    if (existingSelector) {
      existingSelector.remove();
    }

    // Get all columns and their statuses
    const columns = document.querySelectorAll(".task-column");

    // Create the fixed pill navigation for mobile
    const pillNav = document.createElement("div");
    pillNav.className = "column-pill-nav d-md-none";
    pillNav.setAttribute("role", "group");
    pillNav.setAttribute("aria-label", "Column navigation");

    // Generate buttons for each column
    columns.forEach(function (column) {
      const status = column.getAttribute("data-status");
      const headerText =
        column.querySelector(".task-column-header span")?.textContent.trim() ||
        status;
      const count =
        column.querySelector(".task-count")?.textContent.trim() || "0";

      // Determine button color based on column type
      let buttonClass = "btn-outline-secondary";
      let badgeClass = "bg-secondary";

      if (column.classList.contains("column-todo")) {
        buttonClass = "btn-outline-secondary";
        badgeClass = "bg-secondary";
      } else if (column.classList.contains("column-in-progress")) {
        buttonClass = "btn-outline-primary";
        badgeClass = "bg-primary";
      } else if (column.classList.contains("column-review")) {
        buttonClass = "btn-outline-warning";
        badgeClass = "bg-warning text-dark";
      } else if (column.classList.contains("column-done")) {
        buttonClass = "btn-outline-success";
        badgeClass = "bg-success";
      }

      const button = document.createElement("button");
      button.type = "button";
      button.className = `btn ${buttonClass}`;
      button.setAttribute("data-column", status);
      button.setAttribute("aria-controls", `${status}-tasks`);
      button.innerHTML = `${headerText} <span class="badge ${badgeClass} ms-1">${count}</span>`;

      // Set "In Progress" as default active state
      if (column.classList.contains("column-in-progress")) {
        button.classList.add("active");
      }

      pillNav.appendChild(button);
    });

    // Add the pill navigation to the document body for fixed positioning
    document.body.appendChild(pillNav);

    // Add event handlers for the pill navigation buttons
    const pillButtons = pillNav.querySelectorAll("button");
    pillButtons.forEach((button) => {
      button.addEventListener("click", function (e) {
        e.preventDefault();

        // Update active state visually
        pillButtons.forEach((btn) => btn.classList.remove("active"));
        this.classList.add("active");

        // Get target column by status
        const columnStatus = this.getAttribute("data-column");
        const targetColumn = document.querySelector(
          `.task-column[data-status="${columnStatus}"]`
        );

        if (targetColumn) {
          // For stacked layout on mobile
          if (window.innerWidth < 768) {
            // Expand the target column and collapse others
            document.querySelectorAll(".task-column").forEach((col) => {
              if (col !== targetColumn) {
                col.classList.add("collapsed");
              }
            });

            // Always expand the target column
            targetColumn.classList.remove("collapsed");

            // Scroll to the target column with offset for fixed headers
            const headerHeight =
              document.querySelector("header")?.offsetHeight || 0;
            const scrollPosition = targetColumn.offsetTop - headerHeight - 15;

            window.scrollTo({
              top: scrollPosition,
              behavior: "smooth",
            });

            // Provide visual feedback
            targetColumn.style.animation = "pulse 0.5s";
            setTimeout(() => {
              targetColumn.style.animation = "";
            }, 500);
          } else {
            // For horizontal layout, scroll horizontally
            const scrollPosition = targetColumn.offsetLeft - 10;
            taskBoard.scrollTo({
              left: scrollPosition,
              behavior: "smooth",
            });
          }
        }
      });
    });

    // Show/hide the navigation based on screen width
    function updateNavigationVisibility() {
      if (window.innerWidth < 768) {
        pillNav.style.display = "flex";
      } else {
        pillNav.style.display = "none";
      }
    }

    // Initial visibility check
    updateNavigationVisibility();

    // Update on resize
    window.addEventListener("resize", updateNavigationVisibility);

    // Highlight the active column when scrolling through the stacked view
    if ("IntersectionObserver" in window) {
      const options = {
        root: null,
        rootMargin: "-10% 0px -70% 0px",
        threshold: 0.1,
      };

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && window.innerWidth < 768) {
            const status = entry.target.getAttribute("data-status");
            pillButtons.forEach((button) => {
              if (button.getAttribute("data-column") === status) {
                button.classList.add("active");
              } else {
                button.classList.remove("active");
              }
            });
          }
        });
      }, options);

      // Observe all columns
      columns.forEach((column) => {
        observer.observe(column);
      });
    }
  }
});
