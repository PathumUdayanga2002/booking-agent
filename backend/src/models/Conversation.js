const mongoose = require("mongoose");

const conversationSchema = new mongoose.Schema(
  {
    userId: { 
      type: String, 
      required: true, 
      index: true, 
      description: "User ID from JWT token" 
    },
    role: { 
      type: String, 
      enum: ["user", "assistant"], 
      required: true,
      description: "Message sender: user or assistant (agent)"
    },
    content: { 
      type: String, 
      required: true,
      description: "Message content"
    },
    metadata: {
      type: Object,
      default: {},
      description: "Additional metadata (tool calls, tool results, etc.)"
    }
  },
  { 
    timestamps: true,
    collection: "conversations"
  }
);

// Index for efficient queries
conversationSchema.index({ userId: 1, createdAt: -1 });

module.exports = mongoose.model("Conversation", conversationSchema);
