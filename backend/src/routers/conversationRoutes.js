const express = require("express");
const router = express.Router();
const { requireAuth } = require("../middleware/auth");
const { conversationSchema } = require("../validators/conversationSchemas");
const conversationService = require("../services/conversationService");
const logger = require("../utils/logger");

/**
 * Save a message to conversation history
 * POST /api/conversations/save
 * Note: No auth required since userId is provided in body (internal service call)
 */
router.post("/save", async (req, res) => {
  try {
    const { userId, role, content, metadata } = req.body;

    // Validate required fields
    if (!userId || !role || !content) {
      return res.status(400).json({
        success: false,
        message: "Missing required fields: userId, role, content"
      });
    }

    if (!["user", "assistant"].includes(role)) {
      return res.status(400).json({
        success: false,
        message: "Invalid role. Must be 'user' or 'assistant'"
      });
    }

    // Save message
    const message = await conversationService.saveMessage(
      userId,
      role,
      content,
      metadata
    );

    res.status(201).json({
      success: true,
      message: "Conversation saved successfully",
      data: message
    });
  } catch (error) {
    logger.error(`✗ Error saving conversation: ${error.message}`);
    res.status(500).json({
      success: false,
      message: "Failed to save conversation",
      error: error.message
    });
  }
});

/**
 * Get conversation history for a user
 * GET /api/conversations/history/:userId?limit=50
 * Note: No auth required - uses userId from path (internal service call from agent)
 */
router.get("/history/:userId", async (req, res) => {
  try {
    const { userId } = req.params;
    const limit = parseInt(req.query.limit) || 50;

    // Get history
    const messages = await conversationService.getConversationHistory(userId, limit);

    res.status(200).json({
      success: true,
      data: messages,
      count: messages.length
    });
  } catch (error) {
    logger.error(`✗ Error retrieving conversation history: ${error.message}`);
    res.status(500).json({
      success: false,
      message: "Failed to retrieve conversation history",
      error: error.message
    });
  }
});

/**
 * Clear conversation history for a user
 * DELETE /api/conversations/history/:userId
 * Note: No auth required - uses userId from path (internal service call)
 */
router.delete("/history/:userId", async (req, res) => {
  try {
    const { userId } = req.params;

    // Clear history
    const deletedCount = await conversationService.clearConversationHistory(userId);

    res.status(200).json({
      success: true,
      message: `Cleared ${deletedCount} messages from conversation history`,
      data: { deletedCount }
    });
  } catch (error) {
    logger.error(`✗ Error clearing conversation history: ${error.message}`);
    res.status(500).json({
      success: false,
      message: "Failed to clear conversation history",
      error: error.message
    });
  }
});

/**
 * Get recent conversations (admin only)
 * GET /api/conversations/admin/recent?limit=100
 */
router.get("/admin/recent", requireAuth, async (req, res) => {
  try {
    // Check admin role (if you have one)
    if (req.user.role !== "admin") {
      return res.status(403).json({
        success: false,
        message: "Unauthorized: Admin access required"
      });
    }

    const limit = parseInt(req.query.limit) || 100;
    const conversations = await conversationService.getRecentConversations(limit);

    res.status(200).json({
      success: true,
      data: conversations,
      count: conversations.length
    });
  } catch (error) {
    logger.error(`✗ Error retrieving recent conversations: ${error.message}`);
    res.status(500).json({
      success: false,
      message: "Failed to retrieve recent conversations",
      error: error.message
    });
  }
});

module.exports = router;
