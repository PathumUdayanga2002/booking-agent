const { z } = require("zod");

/**
 * Zod schema for saving a conversation message
 */
const saveConversationSchema = z.object({
  userId: z
    .string()
    .min(1, "User ID is required")
    .describe("User ID from JWT token"),
  
  role: z
    .enum(["user", "assistant"])
    .describe("Message sender: user or assistant"),
  
  content: z
    .string()
    .min(1, "Message content cannot be empty")
    .describe("Message text content"),
  
  metadata: z
    .object({})
    .optional()
    .default({})
    .describe("Optional metadata like tool calls, results, etc.")
});

/**
 * Zod schema for conversation history query
 */
const conversationHistoryQuerySchema = z.object({
  userId: z
    .string()
    .min(1, "User ID is required"),
  
  limit: z
    .number()
    .int()
    .min(1, "Limit must be at least 1")
    .max(500, "Limit cannot exceed 500")
    .optional()
    .default(50)
});

/**
 * Validation middleware for saving conversation
 */
function validateSaveConversation(req, res, next) {
  try {
    const validationResult = saveConversationSchema.safeParse(req.body);
    
    if (!validationResult.success) {
      return res.status(400).json({
        success: false,
        message: "Validation failed",
        errors: validationResult.error.issues.map(issue => ({
          field: issue.path.join("."),
          message: issue.message
        }))
      });
    }
    
    // Store validated data in request
    req.validatedData = validationResult.data;
    next();
  } catch (error) {
    res.status(500).json({
      success: false,
      message: "Validation error",
      error: error.message
    });
  }
}

/**
 * Export schemas and validators
 */
module.exports = {
  conversationSchema: saveConversationSchema,
  conversationHistoryQuerySchema,
  validateSaveConversation
};
