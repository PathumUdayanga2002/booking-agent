const { randomUUID } = require("crypto");

function timestamp() {
  return new Date().toISOString();
}

function log(level, message, context = {}) {
  const payload = {
    ts: timestamp(),
    level,
    message,
    ...context,
  };

  // Keep logs as JSON so they are easy to search in terminal and log tools.
  console.log(JSON.stringify(payload));
}

function info(message, context) {
  log("info", message, context);
}

function warn(message, context) {
  log("warn", message, context);
}

function error(message, context) {
  log("error", message, context);
}

function createRequestId() {
  return randomUUID();
}

module.exports = {
  info,
  warn,
  error,
  createRequestId,
};
