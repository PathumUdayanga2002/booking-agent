const { z } = require("zod");

const registerUserSchema = z.object({
  name: z.string().min(2).max(80),
  email: z.string().email(),
  password: z.string().min(8).max(128),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128),
});

const registerAdminSchema = z.object({
  name: z.string().min(2).max(80),
  email: z.string().email(),
  password: z.string().min(8).max(128),
  adminKey: z.string().min(6),
});

module.exports = {
  registerUserSchema,
  loginSchema,
  registerAdminSchema,
};
