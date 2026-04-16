const { AppError } = require("../utils/errors");
const { warn } = require("../utils/logger");

function validateBody(schema) {
  return (req, _res, next) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      const message = result.error.issues.map((issue) => issue.message).join(", ");
      warn("Request body validation failed", {
        requestId: req.id,
        errors: result.error.issues,
      });
      return next(new AppError(message || "Invalid request body", 400));
    }

    req.body = result.data;
    next();
  };
}

function validateQuery(schema) {
  return (req, _res, next) => {
    const result = schema.safeParse(req.query);
    if (!result.success) {
      const message = result.error.issues.map((issue) => issue.message).join(", ");
      warn("Request query validation failed", {
        requestId: req.id,
        errors: result.error.issues,
      });
      return next(new AppError(message || "Invalid query", 400));
    }

    req.query = result.data;
    next();
  };
}

module.exports = {
  validateBody,
  validateQuery,
};
