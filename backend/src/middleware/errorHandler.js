const { AppError } = require("../utils/errors");
const { error: logError, warn } = require("../utils/logger");

function notFound(_req, _res, next) {
  next(new AppError("Route not found", 404));
}

function errorHandler(error, req, res, _next) {
  const statusCode = error.statusCode || 500;
  const requestId = req.id || "unknown";

  if (error.name === "ValidationError") {
    warn("Validation failed", { requestId, error: error.message });
    return res.status(400).json({
      success: false,
      message: error.message,
    });
  }

  if (error.code === 11000) {
    warn("Duplicate key error", {
      requestId,
      code: error.code,
      message: error.message,
    });
    return res.status(409).json({
      success: false,
      message: "Email already registered. Try logging in or use a different email.",
    });
  }

  logError("Request failed", {
    requestId,
    statusCode,
    message: error.message,
    stack: error.stack,
    errorName: error.name,
  });

  res.status(statusCode).json({
    success: false,
    message: error.message || "Internal server error",
    requestId,
  });
}

module.exports = {
  notFound,
  errorHandler,
};
