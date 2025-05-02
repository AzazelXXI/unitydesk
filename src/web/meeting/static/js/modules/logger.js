/**
 * Logger Module
 * Provides centralized logging with configurable verbosity
 */

// Log levels
export const LOG_LEVELS = {
    ERROR: 0,
    WARN: 1,
    INFO: 2,
    DEBUG: 3,
    TRACE: 4
};

// Current log level - change this to control verbosity
// For production, set to LOG_LEVELS.ERROR or LOG_LEVELS.WARN
// For development, you might want LOG_LEVELS.INFO or LOG_LEVELS.DEBUG
// For detailed troubleshooting, use LOG_LEVELS.TRACE
let currentLogLevel = LOG_LEVELS.TRACE;

/**
 * Set the current log level
 * @param {number} level - The log level to set
 */
export const setLogLevel = (level) => {
    if (Object.values(LOG_LEVELS).includes(level)) {
        currentLogLevel = level;
    } else {
        console.error(`Invalid log level: ${level}`);
    }
};

/**
 * Logger object with methods for each log level
 */
export const logger = {
    error: (message, ...args) => {
        if (currentLogLevel >= LOG_LEVELS.ERROR) {
            console.error(`[ERROR] ${message}`, ...args);
        }
    },
    
    warn: (message, ...args) => {
        if (currentLogLevel >= LOG_LEVELS.WARN) {
            console.warn(`[WARN] ${message}`, ...args);
        }
    },
    
    info: (message, ...args) => {
        if (currentLogLevel >= LOG_LEVELS.INFO) {
            console.log(`[INFO] ${message}`, ...args);
        }
    },
    
    debug: (message, ...args) => {
        if (currentLogLevel >= LOG_LEVELS.DEBUG) {
            console.log(`[DEBUG] ${message}`, ...args);
        }
    },
    
    trace: (message, ...args) => {
        if (currentLogLevel >= LOG_LEVELS.TRACE) {
            console.log(`[TRACE] ${message}`, ...args);
        }
    }
};
