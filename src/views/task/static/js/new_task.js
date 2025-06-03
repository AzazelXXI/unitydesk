document.addEventListener("DOMContentLoaded", function () {
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

  // Check if we're on a mobile device
  const isMobile = isMobileDevice();
  if (isMobile) {
    // Enhance form elements for touch devices
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
});
