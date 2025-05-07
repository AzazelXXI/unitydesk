/**
 * Notification UI Components
 * 
 * This file contains JS components for displaying notifications in the UI,
 * including a notification bell icon with unread count, dropdown panel,
 * and individual notification items.
 */

class NotificationSystem {
  constructor(options = {}) {
    this.options = {
      apiBaseUrl: '/api',
      wsBaseUrl: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`,
      userId: null,
      containerSelector: '#notification-container',
      maxNotifications: 20,
      ...options
    };
    
    this.state = {
      notifications: [],
      unreadCount: 0,
      isOpen: false,
      isLoading: false,
      socket: null,
      isConnected: false,
      error: null
    };
    
    // Initialize UI
    this.init();
  }
  
  /**
   * Initialize the notification system
   */
  init() {
    // Create UI components
    this.createElements();
    
    // Bind events
    this.bindEvents();
    
    // Load initial notifications
    if (this.options.userId) {
      this.loadNotifications();
      this.connectWebSocket();
    }
  }
  
  /**
   * Create notification UI elements
   */
  createElements() {
    const container = document.querySelector(this.options.containerSelector);
    if (!container) {
      console.error('Notification container not found:', this.options.containerSelector);
      return;
    }
    
    // Create main notification wrapper
    this.wrapper = document.createElement('div');
    this.wrapper.className = 'notification-wrapper';
    
    // Create notification bell button
    this.bellButton = document.createElement('button');
    this.bellButton.className = 'notification-bell';
    this.bellButton.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="bell-icon">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
      </svg>
      <span class="notification-badge">0</span>
    `;
    this.wrapper.appendChild(this.bellButton);
    
    // Create notification dropdown panel
    this.dropdown = document.createElement('div');
    this.dropdown.className = 'notification-dropdown';
    
    // Dropdown header
    this.dropdownHeader = document.createElement('div');
    this.dropdownHeader.className = 'notification-header';
    this.dropdownHeader.innerHTML = `
      <h3>Notifications</h3>
      <div class="notification-actions">
        <button class="mark-all-read">Mark all as read</button>
        <button class="notification-settings">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
        </button>
      </div>
    `;
    this.dropdown.appendChild(this.dropdownHeader);
    
    // Notification filters
    this.dropdownFilters = document.createElement('div');
    this.dropdownFilters.className = 'notification-filters';
    this.dropdownFilters.innerHTML = `
      <button class="filter active" data-filter="all">All</button>
      <button class="filter" data-filter="unread">Unread</button>
      <button class="filter" data-filter="mentions">Mentions</button>
    `;
    this.dropdown.appendChild(this.dropdownFilters);
    
    // Notification list container
    this.notificationList = document.createElement('div');
    this.notificationList.className = 'notification-list';
    this.dropdown.appendChild(this.notificationList);
    
    // Loading indicator
    this.loadingIndicator = document.createElement('div');
    this.loadingIndicator.className = 'notification-loading';
    this.loadingIndicator.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="loader">
        <line x1="12" y1="2" x2="12" y2="6"></line>
        <line x1="12" y1="18" x2="12" y2="22"></line>
        <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
        <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
        <line x1="2" y1="12" x2="6" y2="12"></line>
        <line x1="18" y1="12" x2="22" y2="12"></line>
        <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
        <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
      </svg>
      <span>Loading notifications...</span>
    `;
    this.notificationList.appendChild(this.loadingIndicator);
    
    // Empty state
    this.emptyState = document.createElement('div');
    this.emptyState.className = 'notification-empty-state';
    this.emptyState.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
      </svg>
      <p>No notifications yet</p>
    `;
    this.notificationList.appendChild(this.emptyState);
    
    // Dropdown footer
    this.dropdownFooter = document.createElement('div');
    this.dropdownFooter.className = 'notification-footer';
    this.dropdownFooter.innerHTML = `
      <a href="/notifications" class="view-all">View all notifications</a>
    `;
    this.dropdown.appendChild(this.dropdownFooter);
    
    // Add dropdown to wrapper
    this.wrapper.appendChild(this.dropdown);
    
    // Add wrapper to container
    container.appendChild(this.wrapper);
    
    // Initial state
    this.updateBadge();
    this.hideDropdown();
    this.hideLoading();
  }
  
  /**
   * Bind event listeners
   */
  bindEvents() {
    // Toggle dropdown when clicking bell
    this.bellButton.addEventListener('click', () => {
      if (this.state.isOpen) {
        this.hideDropdown();
      } else {
        this.showDropdown();
      }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (event) => {
      if (this.state.isOpen && !this.wrapper.contains(event.target)) {
        this.hideDropdown();
      }
    });
    
    // Mark all as read
    const markAllReadBtn = this.dropdownHeader.querySelector('.mark-all-read');
    markAllReadBtn.addEventListener('click', () => {
      this.markAllAsRead();
    });
    
    // Settings button
    const settingsBtn = this.dropdownHeader.querySelector('.notification-settings');
    settingsBtn.addEventListener('click', () => {
      window.location.href = '/settings/notifications';
    });
    
    // Filters
    const filters = this.dropdownFilters.querySelectorAll('.filter');
    filters.forEach(filter => {
      filter.addEventListener('click', () => {
        // Update active filter
        filters.forEach(f => f.classList.remove('active'));
        filter.classList.add('active');
        
        // Apply filter
        const filterType = filter.getAttribute('data-filter');
        this.applyFilter(filterType);
      });
    });
  }
  
  /**
   * Load notifications from API
   */
  loadNotifications() {
    if (!this.options.userId) return;
    
    this.setState({ isLoading: true, error: null });
    this.showLoading();
    
    fetch(`${this.options.apiBaseUrl}/notifications/user/${this.options.userId}?limit=${this.options.maxNotifications}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to load notifications');
        }
        return response.json();
      })
      .then(data => {
        this.setState({ 
          notifications: data, 
          isLoading: false 
        });
        this.renderNotifications();
        this.updateUnreadCount();
      })
      .catch(error => {
        console.error('Error loading notifications:', error);
        this.setState({ 
          error: error.message,
          isLoading: false 
        });
        this.renderError();
      });
  }
  
  /**
   * Get notification counts
   */
  loadNotificationCounts() {
    if (!this.options.userId) return;
    
    fetch(`${this.options.apiBaseUrl}/notifications/user/${this.options.userId}/count`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to load notification counts');
        }
        return response.json();
      })
      .then(data => {
        this.setState({ unreadCount: data.unread });
        this.updateBadge();
      })
      .catch(error => {
        console.error('Error loading notification counts:', error);
      });
  }
  
  /**
   * Connect to WebSocket for real-time notifications
   */
  connectWebSocket() {
    if (!this.options.userId) return;
    
    const wsUrl = `${this.options.wsBaseUrl}/notifications/${this.options.userId}`;
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
      console.log('Notification WebSocket connected');
      this.setState({ isConnected: true });
    };
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'notification') {
        // New notification received
        this.handleNewNotification(data.data);
      } else if (data.type === 'notification_update') {
        // Notification updated
        this.handleNotificationUpdate(data.notification_id, data.update_type);
      } else if (data.type === 'notification_count') {
        // Update counts
        this.setState({ unreadCount: data.counts.unread });
        this.updateBadge();
      }
    };
    
    socket.onclose = () => {
      console.log('Notification WebSocket disconnected');
      this.setState({ isConnected: false });
      
      // Try to reconnect after a delay
      setTimeout(() => {
        this.connectWebSocket();
      }, 3000);
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.setState({ socket });
  }
  
  /**
   * Handle new notification from WebSocket
   */
  handleNewNotification(notification) {
    // Update notifications list
    const notifications = [notification, ...this.state.notifications];
    if (notifications.length > this.options.maxNotifications) {
      notifications.pop();
    }
    
    this.setState({ 
      notifications,
      unreadCount: this.state.unreadCount + 1
    });
    
    // Update UI
    this.renderNotifications();
    this.updateBadge();
    
    // Show notification toast
    this.showNotificationToast(notification);
  }
  
  /**
   * Handle notification update from WebSocket
   */
  handleNotificationUpdate(notificationId, updateType) {
    if (updateType === 'read') {
      // Mark notification as read
      const notifications = this.state.notifications.map(n => {
        if (n.id === notificationId && !n.read_at) {
          return { ...n, read_at: new Date().toISOString() };
        }
        return n;
      });
      
      this.setState({ 
        notifications,
        unreadCount: Math.max(0, this.state.unreadCount - 1)
      });
      
      // Update UI
      this.renderNotifications();
      this.updateBadge();
    }
  }
  
  /**
   * Mark notification as read
   */
  markAsRead(notificationId) {
    if (!this.options.userId) return;
    
    fetch(`${this.options.apiBaseUrl}/notifications/${notificationId}/mark-read`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: this.options.userId })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to mark notification as read');
        }
        return response.json();
      })
      .then(() => {
        // Update locally
        const notifications = this.state.notifications.map(n => {
          if (n.id === notificationId && !n.read_at) {
            return { ...n, read_at: new Date().toISOString() };
          }
          return n;
        });
        
        this.setState({ 
          notifications,
          unreadCount: Math.max(0, this.state.unreadCount - 1)
        });
        
        // Update UI
        this.renderNotifications();
        this.updateBadge();
      })
      .catch(error => {
        console.error('Error marking notification as read:', error);
      });
  }
  
  /**
   * Mark all notifications as read
   */
  markAllAsRead() {
    if (!this.options.userId) return;
    
    fetch(`${this.options.apiBaseUrl}/notifications/user/${this.options.userId}/mark-all-read`, {
      method: 'PUT'
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to mark all notifications as read');
        }
        return response.json();
      })
      .then(() => {
        // Update locally
        const now = new Date().toISOString();
        const notifications = this.state.notifications.map(n => {
          if (!n.read_at) {
            return { ...n, read_at: now };
          }
          return n;
        });
        
        this.setState({ 
          notifications,
          unreadCount: 0
        });
        
        // Update UI
        this.renderNotifications();
        this.updateBadge();
      })
      .catch(error => {
        console.error('Error marking all notifications as read:', error);
      });
  }
  
  /**
   * Delete notification
   */
  deleteNotification(notificationId) {
    if (!this.options.userId) return;
    
    fetch(`${this.options.apiBaseUrl}/notifications/${notificationId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: this.options.userId })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to delete notification');
        }
        return response.json();
      })
      .then(() => {
        // Update locally
        const notifications = this.state.notifications.filter(n => n.id !== notificationId);
        const wasUnread = this.state.notifications.find(n => n.id === notificationId && !n.read_at);
        
        this.setState({ 
          notifications,
          unreadCount: wasUnread ? Math.max(0, this.state.unreadCount - 1) : this.state.unreadCount
        });
        
        // Update UI
        this.renderNotifications();
        this.updateBadge();
      })
      .catch(error => {
        console.error('Error deleting notification:', error);
      });
  }
  
  /**
   * Apply filter to notifications
   */
  applyFilter(filterType) {
    this.renderNotifications(filterType);
  }
  
  /**
   * Render notifications in the dropdown
   */
  renderNotifications(filterType = 'all') {
    // Clear existing notifications
    const existingItems = this.notificationList.querySelectorAll('.notification-item');
    existingItems.forEach(item => item.remove());
    
    // Get filtered notifications
    let notifications = [...this.state.notifications];
    if (filterType === 'unread') {
      notifications = notifications.filter(n => !n.read_at);
    } else if (filterType === 'mentions') {
      notifications = notifications.filter(n => n.type === 'mention');
    }
    
    // Show empty state if no notifications
    if (notifications.length === 0) {
      this.showEmptyState();
    } else {
      this.hideEmptyState();
      
      // Render notifications
      notifications.forEach(notification => {
        const notificationItem = this.createNotificationItem(notification);
        
        // Insert after the loading indicator and empty state
        this.notificationList.appendChild(notificationItem);
      });
    }
  }
  
  /**
   * Create notification item element
   */
  createNotificationItem(notification) {
    const isUnread = !notification.read_at;
    
    const item = document.createElement('div');
    item.className = `notification-item ${isUnread ? 'unread' : 'read'}`;
    item.setAttribute('data-notification-id', notification.id);
    item.setAttribute('data-notification-type', notification.type || 'default');
    
    // Priority class
    if (notification.priority) {
      item.classList.add(`priority-${notification.priority}`);
    }
    
    // Icon
    const iconName = notification.icon || this.getDefaultIconForType(notification.type);
    
    // Timestamp
    const timeAgo = this.formatTimeAgo(notification.created_at);
    
    // Content
    item.innerHTML = `
      <div class="notification-icon">
        <svg class="icon icon-${iconName}">
          <use xlink:href="/static/icons.svg#${iconName}"></use>
        </svg>
      </div>
      <div class="notification-content">
        <div class="notification-title">${notification.title}</div>
        <div class="notification-text">${notification.content}</div>
        <div class="notification-meta">
          <span class="notification-time">${timeAgo}</span>
        </div>
      </div>
      <div class="notification-actions">
        <button class="notification-mark-read" title="${isUnread ? 'Mark as read' : 'Mark as unread'}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${isUnread ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>' : '<circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="3"></circle>'}
          </svg>
        </button>
        <button class="notification-delete" title="Remove notification">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    `;
    
    // Bind events for this notification item
    this.bindNotificationItemEvents(item, notification);
    
    return item;
  }
  
  /**
   * Bind events for notification item
   */
  bindNotificationItemEvents(element, notification) {
    // Click notification to navigate
    element.addEventListener('click', (event) => {
      if (!event.target.closest('.notification-actions')) {
        // Mark as read
        if (!notification.read_at) {
          this.markAsRead(notification.id);
        }
        
        // Navigate to action URL if present
        if (notification.action_url) {
          window.location.href = notification.action_url;
        }
      }
    });
    
    // Mark as read button
    const markReadBtn = element.querySelector('.notification-mark-read');
    if (markReadBtn) {
      markReadBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        if (!notification.read_at) {
          this.markAsRead(notification.id);
        } else {
          // TODO: Mark as unread functionality could be added here
        }
      });
    }
    
    // Delete button
    const deleteBtn = element.querySelector('.notification-delete');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        this.deleteNotification(notification.id);
      });
    }
  }
  
  /**
   * Show notification as a toast
   */
  showNotificationToast(notification) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('notification-toasts');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'notification-toasts';
      document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = 'notification-toast';
    
    // Add priority class if present
    if (notification.priority) {
      toast.classList.add(`priority-${notification.priority}`);
    }
    
    // Icon
    const iconName = notification.icon || this.getDefaultIconForType(notification.type);
    
    // Toast content
    toast.innerHTML = `
      <div class="toast-icon">
        <svg class="icon icon-${iconName}">
          <use xlink:href="/static/icons.svg#${iconName}"></use>
        </svg>
      </div>
      <div class="toast-content">
        <div class="toast-title">${notification.title}</div>
        <div class="toast-text">${notification.content}</div>
      </div>
      <button class="toast-close">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Animation
    setTimeout(() => {
      toast.classList.add('show');
    }, 10);
    
    // Close button
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
      toast.classList.remove('show');
      setTimeout(() => {
        toast.remove();
      }, 300);
    });
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.classList.remove('show');
        setTimeout(() => {
          if (toast.parentNode) {
            toast.remove();
          }
        }, 300);
      }
    }, 5000);
    
    // Click to navigate
    toast.addEventListener('click', (event) => {
      if (!event.target.closest('.toast-close')) {
        // Mark as read
        this.markAsRead(notification.id);
        
        // Navigate to action URL if present
        if (notification.action_url) {
          window.location.href = notification.action_url;
        }
        
        // Hide toast
        toast.classList.remove('show');
        setTimeout(() => {
          toast.remove();
        }, 300);
      }
    });
  }
  
  /**
   * Toggle dropdown display
   */
  showDropdown() {
    this.dropdown.classList.add('open');
    this.state.isOpen = true;
    
    // Load fresh notifications when opening
    this.loadNotifications();
    
    // Mark as seen (still unread, but seen in dropdown)
    this.bellButton.classList.remove('has-new');
  }
  
  hideDropdown() {
    this.dropdown.classList.remove('open');
    this.state.isOpen = false;
  }
  
  /**
   * Show/hide loading indicator
   */
  showLoading() {
    this.loadingIndicator.style.display = 'flex';
  }
  
  hideLoading() {
    this.loadingIndicator.style.display = 'none';
  }
  
  /**
   * Show/hide empty state
   */
  showEmptyState() {
    this.emptyState.style.display = 'flex';
  }
  
  hideEmptyState() {
    this.emptyState.style.display = 'none';
  }
  
  /**
   * Show error message
   */
  renderError() {
    this.hideLoading();
    
    // Create or update error element
    let errorEl = this.notificationList.querySelector('.notification-error');
    if (!errorEl) {
      errorEl = document.createElement('div');
      errorEl.className = 'notification-error';
      this.notificationList.appendChild(errorEl);
    }
    
    errorEl.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <p>${this.state.error || 'Failed to load notifications'}</p>
      <button class="retry-button">Retry</button>
    `;
    
    // Retry button
    const retryBtn = errorEl.querySelector('.retry-button');
    retryBtn.addEventListener('click', () => {
      this.loadNotifications();
    });
    
    // Show error
    errorEl.style.display = 'flex';
  }
  
  /**
   * Update notification badge count
   */
  updateBadge() {
    const badge = this.bellButton.querySelector('.notification-badge');
    const count = this.state.unreadCount;
    
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.classList.add('show');
      
      // Add visual indicator
      this.bellButton.classList.add('has-unread');
    } else {
      badge.textContent = '0';
      badge.classList.remove('show');
      this.bellButton.classList.remove('has-unread');
    }
  }
  
  /**
   * Count unread notifications
   */
  updateUnreadCount() {
    const unreadCount = this.state.notifications.filter(n => !n.read_at).length;
    this.setState({ unreadCount });
    this.updateBadge();
  }
  
  /**
   * Update state and trigger UI updates
   */
  setState(newState) {
    this.state = {
      ...this.state,
      ...newState
    };
  }
  
  /**
   * Format timestamp to relative time string
   */
  formatTimeAgo(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) {
      return 'just now';
    }
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
      return `${minutes}m ago`;
    }
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
      return `${hours}h ago`;
    }
    
    const days = Math.floor(hours / 24);
    if (days < 30) {
      return `${days}d ago`;
    }
    
    // For older dates, show actual date
    return date.toLocaleDateString();
  }
  
  /**
   * Get default icon for notification type
   */
  getDefaultIconForType(type) {
    const icons = {
      'system': 'info',
      'task': 'clipboard',
      'message': 'message-circle',
      'meeting': 'calendar',
      'document': 'file-text',
      'project': 'briefcase',
      'department': 'users',
      'mention': 'at-sign'
    };
    
    return icons[type] || 'bell';
  }
}

// Initialize notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Get user ID from data attribute or some other source
  const userId = document.body.getAttribute('data-user-id');
  
  if (userId) {
    window.notificationSystem = new NotificationSystem({
      userId: userId,
      containerSelector: '#header-notifications'
    });
  }
});
