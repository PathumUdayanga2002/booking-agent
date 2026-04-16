const mongoose = require("mongoose");
const { mongodbUri } = require("./env");
const { info, error: logError } = require("../utils/logger");

async function connectDatabase() {
  try {
    info("Connecting to MongoDB", { uri: mongodbUri.replace(/:[^:]+@/, ":***@") });

    const connection = await mongoose.connect(mongodbUri, {
      autoIndex: true,
    });

    info("MongoDB connected successfully", {
      host: connection.connection.host,
      database: connection.connection.db.databaseName,
    });

    return connection;
  } catch (err) {
    logError("Failed to connect to MongoDB", {
      error: err.message,
      code: err.code,
      stack: err.stack,
    });
    throw err;
  }
}

module.exports = {
  connectDatabase,
};
