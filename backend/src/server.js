const app = require("./app");
const { connectDatabase } = require("./config/db");
const { port } = require("./config/env");
const { info, error: logError } = require("./utils/logger");

async function bootstrap() {
  try {
    info("Starting backend server", { version: "1.0.0" });
    
    await connectDatabase();
    
    app.listen(port, () => {
      info("Backend API ready", {
        port,
        url: `http://localhost:${port}`,
        health: `http://localhost:${port}/health`,
        apiBase: `http://localhost:${port}/api`,
      });
    });
  } catch (err) {
    logError("Bootstrap failed", {
      error: err instanceof Error ? err.message : String(err),
      stack: err instanceof Error ? err.stack : undefined,
    });
    process.exit(1);
  }
}

bootstrap();
