const express = require("express");
const { asyncHandler } = require("../utils/asyncHandler");
const { validateBody } = require("../middleware/validate");
const { requireAuth } = require("../middleware/auth");
const {
  registerUserSchema,
  loginSchema,
  registerAdminSchema,
} = require("../validators/authSchemas");
const {
  registerUser,
  registerAdmin,
  login,
  me,
} = require("../controllers/authController");

const router = express.Router();

router.post("/register", validateBody(registerUserSchema), asyncHandler(registerUser));
router.post("/login", validateBody(loginSchema), asyncHandler(login));
router.post(
  "/admin/register-temp",
  validateBody(registerAdminSchema),
  asyncHandler(registerAdmin)
);
router.get("/me", requireAuth, asyncHandler(me));

module.exports = router;
