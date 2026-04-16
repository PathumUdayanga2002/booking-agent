const jwt = require("jsonwebtoken");
const User = require("../models/User");
const { jwtSecret, jwtExpiresIn, tempAdminKey } = require("../config/env");
const { AppError } = require("../utils/errors");
const { info, warn, error: logError } = require("../utils/logger");

function createToken(userId, role = "user") {
  return jwt.sign({ userId, role }, jwtSecret, { expiresIn: jwtExpiresIn });
}

function sanitizeUser(user) {
  return {
    id: user._id,
    name: user.name,
    email: user.email,
    role: user.role,
  };
}

async function registerUser(req, res) {
  const { name, email, password } = req.body;
  const requestId = req.id || "unknown";

  info("User registration attempt", { requestId, email, name });

  const existingUser = await User.findOne({ email: email.toLowerCase() });
  if (existingUser) {
    warn("Registration failed - email already exists", { requestId, email });
    throw new AppError("Email is already registered. Please login instead.", 409);
  }

  try {
    const user = await User.create({
      name,
      email: email.toLowerCase(),
      password,
      role: "user",
    });

    info("User created successfully", { requestId, userId: user._id, email });

    const token = createToken(user._id.toString(), user.role);

    res.status(201).json({
      success: true,
      token,
      user: sanitizeUser(user),
    });
  } catch (dbError) {
    logError("Database error during user creation", {
      requestId,
      email,
      errorMessage: dbError.message,
      errorCode: dbError.code,
    });
    throw new AppError("Failed to create user. Please try again.", 500);
  }
}

async function registerAdmin(req, res) {
  const { name, email, password, adminKey } = req.body;
  const requestId = req.id || "unknown";

  info("Admin registration attempt", { requestId, email, name });

  if (adminKey !== tempAdminKey) {
    warn("Admin registration failed - invalid key", { requestId, email });
    throw new AppError("Invalid admin registration key. Contact your administrator.", 403);
  }

  const existingUser = await User.findOne({ email: email.toLowerCase() });
  if (existingUser) {
    warn("Admin registration failed - email exists", { requestId, email });
    throw new AppError("Email is already registered. Please login instead.", 409);
  }

  try {
    const user = await User.create({
      name,
      email: email.toLowerCase(),
      password,
      role: "admin",
    });

    info("Admin created successfully", { requestId, userId: user._id, email });

    const token = createToken(user._id.toString(), user.role);

    res.status(201).json({
      success: true,
      token,
      user: sanitizeUser(user),
    });
  } catch (dbError) {
    logError("Database error during admin creation", {
      requestId,
      email,
      errorMessage: dbError.message,
      errorCode: dbError.code,
    });
    throw new AppError("Failed to create admin account. Please try again.", 500);
  }
}

async function login(req, res) {
  const { email, password } = req.body;
  const requestId = req.id || "unknown";

  info("Login attempt", { requestId, email });

  const user = await User.findOne({ email: email.toLowerCase() });
  if (!user) {
    warn("Login failed - user not found", { requestId, email });
    throw new AppError("Invalid email or password. Check your credentials or register first.", 401);
  }

  const isPasswordValid = await user.comparePassword(password);
  if (!isPasswordValid) {
    warn("Login failed - invalid password", { requestId, email, userId: user._id });
    throw new AppError("Invalid email or password. Check your credentials.", 401);
  }

  info("Login successful", { requestId, email, userId: user._id, role: user.role });

  const token = createToken(user._id.toString(), user.role);

  res.json({
    success: true,
    token,
    user: sanitizeUser(user),
  });
}

async function me(req, res) {
  const requestId = req.id || "unknown";
  info("User info requested", { requestId, userId: req.user._id });

  res.json({
    success: true,
    user: req.user,
  });
}

module.exports = {
  registerUser,
  registerAdmin,
  login,
  me,
};
