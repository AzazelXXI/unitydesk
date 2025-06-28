// JavaScript for Projects Dashboard: filter, sort, search, and modal logic
// Moved from projects.html for maintainability

// Filter and sorting functions
function clearFilters() {
  // Reset all form fields
  document.getElementById("search").value = "";
  document.getElementById("status").value = "all";
  document.getElementById("sort_by").value = "created_at";
  document.getElementById("sort_order").value = "desc";
  // Submit the form to apply cleared filters
  document.getElementById("filterForm").submit();
}

// Auto-submit on select changes for better UX
document.addEventListener("DOMContentLoaded", function () {
  const selects = document.querySelectorAll("#status, #sort_by, #sort_order");
  selects.forEach((select) => {
    select.addEventListener("change", function () {
      document.getElementById("filterForm").submit();
    });
  });

  // Add debounced search
  let searchTimeout;
  const searchInput = document.getElementById("search");
  searchInput.addEventListener("input", function () {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      document.getElementById("filterForm").submit();
    }, 500); // 500ms delay
  });

  // Handle Enter key in search
  searchInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      clearTimeout(searchTimeout);
      document.getElementById("filterForm").submit();
    }
  });
});

document.addEventListener("DOMContentLoaded", function () {
  // Check if we came from project creation (look for hash fragment)
  if (window.location.hash === "#project-created") {
    // Show the success modal
    const modal = new bootstrap.Modal(
      document.getElementById("projectCreatedModal")
    );
    modal.show();
    // Clean up the URL hash without affecting browser history
    history.replaceState(null, "", window.location.pathname);
  }
});
