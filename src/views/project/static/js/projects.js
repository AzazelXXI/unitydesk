// Projects Dashboard JavaScript
document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 Projects Dashboard loaded");

  // Initialize projects dashboard
  initializeProjectsDashboard();

  // Add event listeners
  addProjectEventListeners();
});

/**
 * Initialize the projects dashboard
 */
function initializeProjectsDashboard() {
  // Add loading states to project cards
  const projectCards = document.querySelectorAll(".project-card");
  projectCards.forEach((card, index) => {
    // Add animation delay
    card.style.animationDelay = `${index * 0.1}s`;

    // Add hover effects
    card.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-8px)";
    });

    card.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)";
    });
  });

  // Animate statistics cards
  animateStatsCards();

  console.log(`📊 Loaded ${projectCards.length} project cards`);
}

/**
 * Add event listeners for project interactions
 */
function addProjectEventListeners() {
  // Quick action buttons
  const actionButtons = document.querySelectorAll(".project-actions .btn");
  actionButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent card click when clicking action buttons
    });
  });

  // Project card click to view details
  const projectCards = document.querySelectorAll(".project-card");
  projectCards.forEach((card) => {
    card.addEventListener("click", function (e) {
      // Don't trigger if clicking on action buttons
      if (e.target.closest(".project-actions")) return;

      const projectLink = this.querySelector(".project-title a");
      if (projectLink) {
        window.location.href = projectLink.href;
      }
    });
  });

  // New project button
  const newProjectBtn = document.querySelector('a[href="/projects/new"]');
  if (newProjectBtn) {
    newProjectBtn.addEventListener("click", function (e) {
      // Add loading state
      this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating...';
    });
  }
}

/**
 * Animate statistics cards on load
 */
function animateStatsCards() {
  const statsCards = document.querySelectorAll(".stats-card");

  statsCards.forEach((card, index) => {
    const numberElement = card.querySelector(".stats-number");
    if (numberElement) {
      const finalValue =
        parseInt(numberElement.textContent.replace(/[^\d]/g, "")) || 0;

      // Animate number counting
      setTimeout(() => {
        animateNumber(numberElement, 0, finalValue, 1000);
      }, index * 200);
    }
  });
}

/**
 * Animate number counting effect
 */
function animateNumber(element, start, end, duration) {
  const range = end - start;
  const startTime = performance.now();

  function updateNumber(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Easing function (ease out)
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(start + range * easeOut);

    // Format number with commas for large numbers
    const formattedNumber = current.toLocaleString();

    // Check if it's a currency or percentage
    const originalText = element.textContent;
    if (originalText.includes("$")) {
      element.textContent = "$" + formattedNumber;
    } else if (originalText.includes("%")) {
      element.textContent = formattedNumber + "%";
    } else {
      element.textContent = formattedNumber;
    }

    if (progress < 1) {
      requestAnimationFrame(updateNumber);
    }
  }

  requestAnimationFrame(updateNumber);
}

/**
 * Filter projects by status
 */
function filterProjects(status) {
  const projectCards = document.querySelectorAll(".project-card");

  projectCards.forEach((card) => {
    const projectStatus = card.querySelector(".project-status");
    if (projectStatus) {
      const cardStatus = projectStatus.textContent.trim().toLowerCase();
      const filterStatus = status.toLowerCase();

      if (status === "all" || cardStatus === filterStatus) {
        card.style.display = "block";
        card.style.animation = "fadeInUp 0.5s ease forwards";
      } else {
        card.style.display = "none";
      }
    }
  });

  console.log(`🔍 Filtered projects by status: ${status}`);
}

/**
 * Search projects by name
 */
function searchProjects(searchTerm) {
  const projectCards = document.querySelectorAll(".project-card");
  const term = searchTerm.toLowerCase();

  projectCards.forEach((card) => {
    const projectName = card
      .querySelector(".project-title a")
      .textContent.toLowerCase();
    const projectDescription = card
      .querySelector(".project-description")
      .textContent.toLowerCase();

    if (projectName.includes(term) || projectDescription.includes(term)) {
      card.style.display = "block";
      card.style.animation = "fadeInUp 0.5s ease forwards";
    } else {
      card.style.display = "none";
    }
  });

  console.log(`🔍 Searched projects for: "${searchTerm}"`);
}

/**
 * Refresh project statistics
 */
async function refreshStats() {
  try {
    const response = await fetch("/api/projects/stats");
    if (response.ok) {
      const stats = await response.json();
      updateStatsDisplay(stats);
    }
  } catch (error) {
    console.error("Failed to refresh stats:", error);
  }
}

/**
 * Update statistics display
 */
function updateStatsDisplay(stats) {
  const statsCards = document.querySelectorAll(".stats-card");

  // Map of stat types to their new values
  const statTypes = [
    "total",
    "planning",
    "in_progress",
    "completed",
    "total_budget",
    "avg_progress",
  ];

  statsCards.forEach((card, index) => {
    const numberElement = card.querySelector(".stats-number");
    if (numberElement && statTypes[index]) {
      const newValue = stats[statTypes[index]] || 0;

      // Animate to new value
      const currentValue =
        parseInt(numberElement.textContent.replace(/[^\d]/g, "")) || 0;
      animateNumber(numberElement, currentValue, newValue, 800);
    }
  });
}

// Export functions for global use
window.filterProjects = filterProjects;
window.searchProjects = searchProjects;
window.refreshStats = refreshStats;

console.log("📋 Projects dashboard JavaScript loaded successfully");
