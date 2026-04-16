const jwt = require("jsonwebtoken");
const { jwtSecret } = require("../config/env");
const User = require("../models/User");
const { AppError } = require("../utils/errors");
const { asyncHandler } = require("../utils/asyncHandler");

const requireAuth = asyncHandler(async (req, _res, next) => {
  const authHeader = req.headers.authorization || "";

  if (!authHeader.startsWith("Bearer ")) {
    throw new AppError("Unauthorized", 401);
  }

  const token = authHeader.replace("Bearer ", "").trim();
  let payload;

  try {
    payload = jwt.verify(token, jwtSecret);
  } catch (_error) {
    throw new AppError("Invalid or expired token", 401);
  }

  const user = await User.findById(payload.userId).select("_id name email role");
  if (!user) {
    throw new AppError("User not found", 401);
  }

  req.user = user;
  next();
});

function requireRole(...roles) {
  return (req, _res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return next(new AppError("Forbidden", 403));
    }
    next();
  };
}

module.exports = {
  requireAuth,
  requireRole,
};
