const Conversation = require("../models/Conversation");
const logger = require("../utils/logger");

/**
 * Save a message to conversation history
 * @param {string} userId - User ID from JWT
 * @param {string} role - "user" or "assistant"
 * @param {string} content - Message content
 * @param {object} metadata - Optional metadata (tool calls, etc.)
 */
async function saveMessage(userId, role, content, metadata = {}) {
  try {
    const conversation = new Conversation({
      userId,
      role,
      content,
      metadata
    });
    await conversation.save();
    logger.info(`✓ Message saved for user ${userId} (${role})`);
    return conversation;
  } catch (error) {
    logger.error(`✗ Failed to save message: ${error.message}`);
    // Don't throw - allow chat to continue even if history fails
    return null;
  }
}

/**
 * Get conversation history for a user
 * @param {string} userId - User ID from JWT
 * @param {number} limit - Max messages to retrieve (default 50)
 * @returns {array} Array of messages ordered by creation time
 */
async function getConversationHistory(userId, limit = 50) {
  try {
    const messages = await Conversation.find({ userId })
      .sort({ createdAt: 1 })
      .limit(limit)
      .lean();
    
    logger.info(`✓ Retrieved ${messages.length} messages for user ${userId}`);
    return messages;
  } catch (error) {
    logger.error(`✗ Failed to retrieve conversation history: ${error.message}`);
    return [];
  }
}

/**
 * Clear conversation history for a user (optional - be careful with this)
 * @param {string} userId - User ID from JWT
 */
async function clearConversationHistory(userId) {
  try {
    const result = await Conversation.deleteMany({ userId });
    logger.info(`✓ Cleared ${result.deletedCount} messages for user ${userId}`);
    return result.deletedCount;
  } catch (error) {
    logger.error(`✗ Failed to clear conversation history: ${error.message}`);
    return 0;
  }
}

/**
 * Get recent conversations (for admin/analytics)
 * @param {number} limit - Max records
 */
async function getRecentConversations(limit = 100) {
  try {
    const conversations = await Conversation.find()
      .sort({ createdAt: -1 })
      .limit(limit)
      .lean();
    return conversations;
  } catch (error) {
    logger.error(`✗ Failed to retrieve recent conversations: ${error.message}`);
    return [];
  }
}

module.exports = {
  saveMessage,
  getConversationHistory,
  clearConversationHistory,
  getRecentConversations
};
