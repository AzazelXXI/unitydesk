/**
 * CSA Platform Auth Client
 *
 * This client provides authentication functionality for the CSA Platform
 * It includes methods for logging in, registering, and managing user sessions
 * It also includes utility functions for working with JWT tokens
 */

class CSAAuthClient {
  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
    this.tokenKey = "csa_auth_token";
    this.userKey = "csa_user";

    // Automatically load token and user data from localStorage
    this.token = localStorage.getItem(this.tokenKey);
    this.user = JSON.parse(localStorage.getItem(this.userKey) || "null");

    // Bind methods to maintain 'this' context
    this.login = this.login.bind(this);
    this.register = this.register.bind(this);
    this.logout = this.logout.bind(this);
    this.isLoggedIn = this.isLoggedIn.bind(this);
    this.getAuthHeaders = this.getAuthHeaders.bind(this);
    this.fetchUserProfile = this.fetchUserProfile.bind(this);
    this.updateUserProfile = this.updateUserProfile.bind(this);
    this.changePassword = this.changePassword.bind(this);
  }

  /**
   * Authenticate a user with username/email and password
   *
   * @param {string} username - Username or email
   * @param {string} password - User password
   * @returns {Promise<object>} - User data and token
   */
  async login(username, password) {
    try {
      // Prepare form data for token endpoint
      const formData = new FormData();
      formData.append("username", username);
      formData.append("password", password);

      // Send login request
      const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Login failed");
      }

      // Parse response and store token
      const tokenData = await response.json();
      this.token = tokenData.access_token;
      localStorage.setItem(this.tokenKey, this.token);

      // Fetch user profile
      await this.fetchUserProfile();

      return {
        user: this.user,
        token: this.token,
      };
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    }
  }

  /**
   * Register a new user
   *
   * @param {object} userData - User registration data
   * @returns {Promise<object>} - Created user data
   */
  async register(userData) {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Registration failed");
      }

      return await response.json();
    } catch (error) {
      console.error("Registration error:", error);
      throw error;
    }
  }
  /**
   * Log out the current user
   */
  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);

    // Redirect to login page after logout
    window.location.href = "/login";
  }

  /**
   * Check if user is currently logged in
   *
   * @returns {boolean} - True if user is logged in
   */
  isLoggedIn() {
    return !!this.token;
  }

  /**
   * Get authentication headers for API requests
   *
   * @returns {object} - Headers object with Authorization
   */
  getAuthHeaders() {
    return {
      Authorization: `Bearer ${this.token}`,
      "Content-Type": "application/json",
    };
  }

  /**
   * Fetch current user profile
   *
   * @returns {Promise<object>} - User profile data
   */
  async fetchUserProfile() {
    try {
      if (!this.token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`${this.baseUrl}/api/v1/users/me`, {
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid, log out
          this.logout();
        }
        throw new Error("Failed to fetch user profile");
      }

      this.user = await response.json();
      localStorage.setItem(this.userKey, JSON.stringify(this.user));
      return this.user;
    } catch (error) {
      console.error("Profile fetch error:", error);
      throw error;
    }
  }

  /**
   * Update user profile
   *
   * @param {object} profileData - Profile data to update
   * @returns {Promise<object>} - Updated user data
   */
  async updateUserProfile(profileData) {
    try {
      if (!this.token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`${this.baseUrl}/api/v1/users/me`, {
        method: "PUT",
        headers: this.getAuthHeaders(),
        body: JSON.stringify(profileData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update profile");
      }

      const updatedUser = await response.json();
      this.user = updatedUser;
      localStorage.setItem(this.userKey, JSON.stringify(this.user));

      return updatedUser;
    } catch (error) {
      console.error("Profile update error:", error);
      throw error;
    }
  }

  /**
   * Change user password
   *
   * @param {string} currentPassword - Current password
   * @param {string} newPassword - New password
   * @returns {Promise<object>} - Success message
   */
  async changePassword(currentPassword, newPassword) {
    try {
      if (!this.token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(
        `${this.baseUrl}/api/v1/users/me/change-password`,
        {
          method: "POST",
          headers: this.getAuthHeaders(),
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Password change failed");
      }

      return await response.json();
    } catch (error) {
      console.error("Password change error:", error);
      throw error;
    }
  }
}

// Create global instance
const authClient = new CSAAuthClient();
