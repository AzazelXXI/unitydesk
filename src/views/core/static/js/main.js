/**
 * CSA Hello System - Main JavaScript File
 * Contains shared functions and behaviors used across the application
 */

// Global namespace for CSA application
const CSA = {};

// Initialize the application
CSA.init = function () {
    // Set up global event listeners
    document.addEventListener("DOMContentLoaded", function () {
        CSA.setupTooltips();
        CSA.setupPopovers();
        CSA.setupDropdowns();
        CSA.setupSidebar();
        CSA.setupDarkMode();
        CSA.setupNotifications();
        CSA.setupSearchBar();
        CSA.setupFormValidation();
        CSA.setupTableSorting();
        CSA.setupAnimations();
        CSA.setupCardExpand();
        CSA.handleResponsiveLayout();

        // Initialize page specific modules if they exist
        if (CSA.Dashboard) CSA.Dashboard.init();
        if (CSA.Analytics) CSA.Analytics.init();
        if (CSA.Calendar) CSA.Calendar.init();
        if (CSA.Meeting) CSA.Meeting.init();
        if (CSA.Projects) CSA.Projects.init();
        if (CSA.Tasks) CSA.Tasks.init();
        if (CSA.Users) CSA.Users.init();
    });

    // Add window resize event listener
    window.addEventListener("resize", CSA.handleResponsiveLayout);
};

// Bootstrap components initialization
CSA.setupTooltips = function () {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
};

CSA.setupPopovers = function () {
    const popoverTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="popover"]')
    );
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
};

CSA.setupDropdowns = function () {
    const dropdownElementList = [].slice.call(
        document.querySelectorAll(".dropdown-toggle")
    );
    dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
};

// Sidebar toggle functionality
CSA.setupSidebar = function () {
    const sidebarToggle = document.getElementById("sidebarToggle");

    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", function (e) {
            e.preventDefault();
            document.body.classList.toggle("sidebar-toggled");
            document.querySelector(".sidebar").classList.toggle("toggled");

            // Store sidebar state in local storage
            const isSidebarToggled =
                document.body.classList.contains("sidebar-toggled");
            localStorage.setItem("sidebarToggled", isSidebarToggled);
        });

        // Check if the sidebar state is stored
        const isSidebarToggled =
            localStorage.getItem("sidebarToggled") === "true";

        if (isSidebarToggled) {
            document.body.classList.add("sidebar-toggled");
            document.querySelector(".sidebar").classList.add("toggled");
        }

        // Hide sidebar when window is small
        const handleWindowResize = function () {
            if (window.innerWidth < 768) {
                document.body.classList.add("sidebar-toggled");
                document.querySelector(".sidebar").classList.add("toggled");
            } else if (localStorage.getItem("sidebarToggled") !== "true") {
                document.body.classList.remove("sidebar-toggled");
                document.querySelector(".sidebar").classList.remove("toggled");
            }
        };

        window.addEventListener("resize", handleWindowResize);
        handleWindowResize();
    }
};

// Dark mode toggle
CSA.setupDarkMode = function () {
    const darkModeToggle = document.getElementById("darkModeToggle");

    if (darkModeToggle) {
        // Check user preference from local storage
        const isDarkMode = localStorage.getItem("darkMode") === "enabled";

        if (isDarkMode) {
            document.body.classList.add("dark-mode");
            darkModeToggle.checked = true;
        }

        darkModeToggle.addEventListener("change", function () {
            if (this.checked) {
                document.body.classList.add("dark-mode");
                localStorage.setItem("darkMode", "enabled");
            } else {
                document.body.classList.remove("dark-mode");
                localStorage.setItem("darkMode", "disabled");
            }
        });
    }
};

// Notification system
CSA.setupNotifications = function () {
    const notificationBell = document.getElementById("notificationBell");

    if (notificationBell) {
        notificationBell.addEventListener("click", function () {
            // Mark as read when opened
            const unreadBadge = notificationBell.querySelector(".unread-badge");
            if (unreadBadge) {
                unreadBadge.style.display = "none";
            }
        });

        // Demo: Simulate receiving a notification
        CSA.receiveNotification = function (title, message, type = "info") {
            const notificationList =
                document.getElementById("notificationList");

            if (notificationList) {
                const now = new Date();
                const timeStr = now.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                });

                // Create notification element
                const notificationItem = document.createElement("div");
                notificationItem.className = `dropdown-item d-flex align-items-center notification-item notification-${type}`;

                notificationItem.innerHTML = `
                    <div class="me-3">
                        <div class="icon-circle bg-${type}">
                            <i class="fas ${
                                type === "info"
                                    ? "fa-info"
                                    : type === "success"
                                    ? "fa-check"
                                    : type === "warning"
                                    ? "fa-exclamation"
                                    : "fa-times"
                            } text-white"></i>
                        </div>
                    </div>
                    <div>
                        <div class="small text-gray-500">${timeStr}</div>
                        <span class="font-weight-bold">${title}</span>
                        <div class="small text-gray-500">${message}</div>
                    </div>
                `;

                // Add to notification list
                notificationList.prepend(notificationItem);

                // Show unread badge
                const unreadBadge =
                    notificationBell.querySelector(".unread-badge");
                if (unreadBadge) {
                    unreadBadge.style.display = "block";
                    unreadBadge.textContent =
                        parseInt(unreadBadge.textContent || "0") + 1;
                }

                // Show toast notification
                CSA.showToast(title, message, type);
            }
        };
    }

    // Initialize WebSocket connection for real-time notifications
    CSA.initNotificationWebsocket = function () {
        // Check if the browser supports WebSocket
        if ("WebSocket" in window) {
            // Create WebSocket connection
            const protocol =
                window.location.protocol === "https:" ? "wss:" : "ws:";
            const wsUrl = `${protocol}//${window.location.host}/ws/notifications`;

            const ws = new WebSocket(wsUrl);

            ws.onopen = function () {
                console.log("WebSocket connection established");
            };

            ws.onmessage = function (event) {
                try {
                    const notification = JSON.parse(event.data);
                    CSA.receiveNotification(
                        notification.title,
                        notification.message,
                        notification.type || "info"
                    );
                } catch (e) {
                    console.error("Error processing notification:", e);
                }
            };

            ws.onclose = function () {
                console.log("WebSocket connection closed");

                // Try to reconnect after a delay
                setTimeout(CSA.initNotificationWebsocket, 3000);
            };

            ws.onerror = function (error) {
                console.error("WebSocket error:", error);
                ws.close();
            };

            // Store the WebSocket connection for later use
            CSA.notificationWs = ws;
        }
    };

    // Call the WebSocket initialization
    CSA.initNotificationWebsocket();
};

// Toast notification system
CSA.showToast = function (title, message, type = "info") {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector(".toast-container");

    if (!toastContainer) {
        toastContainer = document.createElement("div");
        toastContainer.className =
            "toast-container position-fixed bottom-0 end-0 p-3";
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = "toast" + Date.now();
    const toastEl = document.createElement("div");
    toastEl.className = "toast";
    toastEl.id = toastId;
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");

    // Set toast content based on type
    const bgColor =
        type === "info"
            ? "primary"
            : type === "success"
            ? "success"
            : type === "warning"
            ? "warning"
            : "danger";

    const icon =
        type === "info"
            ? "fa-info-circle"
            : type === "success"
            ? "fa-check-circle"
            : type === "warning"
            ? "fa-exclamation-triangle"
            : "fa-times-circle";

    toastEl.innerHTML = `
        <div class="toast-header bg-${bgColor} text-white">
            <i class="fas ${icon} me-2"></i>
            <strong class="me-auto">${title}</strong>
            <small>Just now</small>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    // Add toast to container
    toastContainer.appendChild(toastEl);

    // Initialize and show toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 5000,
    });

    toast.show();

    // Remove toast element when hidden
    toastEl.addEventListener("hidden.bs.toast", function () {
        toastContainer.removeChild(toastEl);
    });

    return toast;
};

// Search bar functionality
CSA.setupSearchBar = function () {
    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const searchResults = document.getElementById("searchResults");

    if (searchForm && searchInput) {
        // Toggle search results container
        searchInput.addEventListener("focus", function () {
            if (searchResults) {
                searchResults.classList.add("show");
            }
        });

        // Implement search functionality
        let searchTimeout;

        searchInput.addEventListener("input", function () {
            const query = this.value.trim();

            // Clear previous timeout
            clearTimeout(searchTimeout);

            if (query.length < 2) {
                if (searchResults) {
                    searchResults.innerHTML = "";
                }
                return;
            }

            // Set timeout to prevent excessive API calls
            searchTimeout = setTimeout(function () {
                CSA.performSearch(query);
            }, 300);
        });

        // Close search results when clicking outside
        document.addEventListener("click", function (event) {
            if (!searchForm.contains(event.target)) {
                if (searchResults) {
                    searchResults.classList.remove("show");
                }
            }
        });

        // Handle search form submission
        searchForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const query = searchInput.value.trim();

            if (query.length < 2) return;

            // Redirect to search results page
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        });
    }
};

// Search functionality
CSA.performSearch = function (query) {
    const searchResults = document.getElementById("searchResults");

    if (!searchResults) return;

    searchResults.innerHTML =
        '<div class="p-3 text-center"><i class="fas fa-spinner fa-spin me-2"></i>Searching...</div>';

    // Make API call to search endpoint
    fetch(`/api/v1/search?q=${encodeURIComponent(query)}`)
        .then((response) => {
            if (!response.ok) {
                throw new Error("Search failed");
            }
            return response.json();
        })
        .then((data) => {
            if (!data || data.results.length === 0) {
                searchResults.innerHTML =
                    '<div class="p-3 text-center text-muted">No results found</div>';
                return;
            }

            // Display search results
            searchResults.innerHTML = "";

            const categories = {};

            // Group results by category
            data.results.forEach((result) => {
                if (!categories[result.type]) {
                    categories[result.type] = [];
                }

                categories[result.type].push(result);
            });

            // Create category sections
            for (const [category, items] of Object.entries(categories)) {
                const categoryTitle = document.createElement("h6");
                categoryTitle.className = "dropdown-header";
                categoryTitle.textContent =
                    category.charAt(0).toUpperCase() + category.slice(1) + "s";

                searchResults.appendChild(categoryTitle);

                // Add results for this category
                items.slice(0, 3).forEach((item) => {
                    const resultItem = document.createElement("a");
                    resultItem.className = "dropdown-item";
                    resultItem.href = item.url;

                    let icon = "fa-file";

                    if (category === "project") icon = "fa-project-diagram";
                    else if (category === "task") icon = "fa-tasks";
                    else if (category === "user") icon = "fa-user";
                    else if (category === "meeting") icon = "fa-video";

                    resultItem.innerHTML = `
                        <i class="fas ${icon} me-2 text-gray-400"></i>
                        <span>${item.title}</span>
                    `;

                    searchResults.appendChild(resultItem);
                });

                // Add view more link if there are more results
                if (items.length > 3) {
                    const viewMoreLink = document.createElement("a");
                    viewMoreLink.className = "dropdown-item text-primary";
                    viewMoreLink.href = `/search?q=${encodeURIComponent(
                        query
                    )}&type=${category}`;
                    viewMoreLink.innerHTML = `<i class="fas fa-search me-2"></i>View all ${items.length} ${category}s...`;

                    searchResults.appendChild(viewMoreLink);
                }

                // Add separator
                if (
                    Object.keys(categories).indexOf(category) <
                    Object.keys(categories).length - 1
                ) {
                    const divider = document.createElement("div");
                    divider.className = "dropdown-divider";

                    searchResults.appendChild(divider);
                }
            }

            // Add link to full search results page
            const fullSearchLink = document.createElement("a");
            fullSearchLink.className =
                "dropdown-item text-primary bg-light text-center";
            fullSearchLink.href = `/search?q=${encodeURIComponent(query)}`;
            fullSearchLink.innerHTML =
                'See all results <i class="fas fa-arrow-right ms-1"></i>';

            searchResults.appendChild(fullSearchLink);
        })
        .catch((error) => {
            console.error("Search error:", error);
            searchResults.innerHTML =
                '<div class="p-3 text-center text-danger">Error performing search</div>';
        });
};

// Form validation
CSA.setupFormValidation = function () {
    const forms = document.querySelectorAll(".needs-validation");

    Array.from(forms).forEach((form) => {
        form.addEventListener(
            "submit",
            function (event) {
                if (!this.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }

                this.classList.add("was-validated");
            },
            false
        );
    });
};

// Table sorting
CSA.setupTableSorting = function () {
    const tables = document.querySelectorAll("table.sortable");

    tables.forEach((table) => {
        const headers = table.querySelectorAll("th.sortable");

        headers.forEach((header) => {
            header.addEventListener("click", function () {
                const sortDirection =
                    this.getAttribute("data-sort-direction") === "asc"
                        ? "desc"
                        : "asc";
                const columnIndex = Array.from(
                    this.parentNode.children
                ).indexOf(this);

                // Reset all headers
                headers.forEach((h) => {
                    h.removeAttribute("data-sort-direction");
                    h.querySelector("i.sort-icon")?.remove();
                });

                // Set sorting direction and add icon
                this.setAttribute("data-sort-direction", sortDirection);

                // Add sort icon
                const icon = document.createElement("i");
                icon.className = `fas fa-sort-${
                    sortDirection === "asc" ? "up" : "down"
                } ms-1 sort-icon`;
                this.appendChild(icon);

                // Sort the table
                CSA.sortTable(table, columnIndex, sortDirection);
            });
        });
    });
};

// Table sorting function
CSA.sortTable = function (table, columnIndex, sortDirection) {
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();

        // Check if values are numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return sortDirection === "asc" ? aNum - bNum : bNum - aNum;
        }

        // Handle date values (format: MM/DD/YYYY or YYYY-MM-DD)
        const dateRegex =
            /^\d{1,2}[/.-]\d{1,2}[/.-]\d{4}$|^\d{4}[/.-]\d{1,2}[/.-]\d{1,2}$/;

        if (dateRegex.test(aValue) && dateRegex.test(bValue)) {
            const aDate = new Date(aValue);
            const bDate = new Date(bValue);

            return sortDirection === "asc" ? aDate - bDate : bDate - aDate;
        }

        // Sort as strings
        return sortDirection === "asc"
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });

    // Re-append rows in sorted order
    rows.forEach((row) => tbody.appendChild(row));
};

// Setup animations for cards and other elements
CSA.setupAnimations = function () {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll(".card:not(.no-animation)");

    cards.forEach((card, index) => {
        card.style.opacity = "0";
        card.style.transform = "translateY(20px)";
        card.style.transition = "opacity 0.5s ease, transform 0.5s ease";

        // Staggered animation
        setTimeout(() => {
            card.style.opacity = "1";
            card.style.transform = "translateY(0)";
        }, 50 * index);
    });

    // Add animation to list items
    const listItems = document.querySelectorAll(".animate-list-item");

    listItems.forEach((item, index) => {
        item.style.opacity = "0";
        item.style.transform = "translateX(-20px)";
        item.style.transition = "opacity 0.3s ease, transform 0.3s ease";

        // Staggered animation
        setTimeout(() => {
            item.style.opacity = "1";
            item.style.transform = "translateX(0)";
        }, 30 * index);
    });
};

// Card expand/collapse functionality
CSA.setupCardExpand = function () {
    const cardToggleButtons = document.querySelectorAll(".card-toggle");

    cardToggleButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const card = this.closest(".card");
            const cardBody = card.querySelector(".card-body");
            const icon = this.querySelector("i");

            if (card.classList.contains("card-collapsed")) {
                // Expand card
                cardBody.style.display = "block";
                card.classList.remove("card-collapsed");
                icon.classList.remove("fa-plus");
                icon.classList.add("fa-minus");
            } else {
                // Collapse card
                cardBody.style.display = "none";
                card.classList.add("card-collapsed");
                icon.classList.remove("fa-minus");
                icon.classList.add("fa-plus");
            }
        });
    });
};

// Handle responsive layout adjustments
CSA.handleResponsiveLayout = function () {
    const windowWidth = window.innerWidth;

    // Adjust data tables for mobile
    const dataTables = document.querySelectorAll(".table-responsive-custom");

    dataTables.forEach((table) => {
        if (windowWidth < 768) {
            table.classList.add("table-mobile-view");
        } else {
            table.classList.remove("table-mobile-view");
        }
    });

    // Handle mobile menu
    const mobileMenuToggle = document.getElementById("mobileMenuToggle");
    const sidebar = document.querySelector(".sidebar");

    if (mobileMenuToggle && sidebar) {
        if (windowWidth < 768) {
            mobileMenuToggle.style.display = "block";
            sidebar.classList.add("sidebar-mobile");
        } else {
            mobileMenuToggle.style.display = "none";
            sidebar.classList.remove("sidebar-mobile", "show-mobile");
        }

        // Add click event to mobile menu toggle
        mobileMenuToggle.addEventListener("click", function () {
            sidebar.classList.toggle("show-mobile");
        });
    }
};

// Utility functions
CSA.util = {
    // Format date with options
    formatDate: function (date, options = {}) {
        const defaultOptions = {
            year: "numeric",
            month: "short",
            day: "numeric",
        };

        const mergedOptions = { ...defaultOptions, ...options };

        return new Date(date).toLocaleDateString(undefined, mergedOptions);
    },

    // Format time
    formatTime: function (date, options = {}) {
        const defaultOptions = {
            hour: "2-digit",
            minute: "2-digit",
            hour12: true,
        };

        const mergedOptions = { ...defaultOptions, ...options };

        return new Date(date).toLocaleTimeString(undefined, mergedOptions);
    },

    // Format datetime
    formatDateTime: function (date, options = {}) {
        const defaultOptions = {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: true,
        };

        const mergedOptions = { ...defaultOptions, ...options };

        return new Date(date).toLocaleString(undefined, mergedOptions);
    },

    // Format number with commas
    formatNumber: function (number) {
        return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },

    // Format currency
    formatCurrency: function (amount, currencyCode = "USD") {
        return new Intl.NumberFormat(undefined, {
            style: "currency",
            currency: currencyCode,
        }).format(amount);
    },

    // Format percentage
    formatPercentage: function (value) {
        return `${Math.round(value * 100) / 100}%`;
    },

    // Truncate text with ellipsis
    truncateText: function (text, maxLength = 50) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + "...";
    },

    // Copy to clipboard
    copyToClipboard: function (text) {
        return navigator.clipboard.writeText(text);
    },

    // Get query parameter from URL
    getQueryParam: function (param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },

    // Debounce function to limit how often a function can run
    debounce: function (func, wait) {
        let timeout;

        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };

            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
};

// Initialize when DOM is ready
CSA.init();
