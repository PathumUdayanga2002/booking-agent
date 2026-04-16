require("./config/env");

const cors = require("cors");
const express = require("express");
const helmet = require("helmet");
const morgan = require("morgan");
const rateLimit = require("express-rate-limit");
const routes = require("./routes");
const { frontendOrigin } = require("./config/env");
const { notFound, errorHandler } = require("./middleware/errorHandler");
const { createRequestId } = require("./utils/logger");

const app = express();

app.use((req, _res, next) => {
  req.id = createRequestId();
  next();
});

app.use(helmet());
app.use(
  cors({
    origin: frontendOrigin,
    credentials: false,
  })
);
app.use(
  rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 300,
    standardHeaders: true,
    legacyHeaders: false,
  })
);
app.use(express.json({ limit: "500kb" }));
app.use(morgan("dev"));

app.get("/health", (_req, res) => {
  res.json({
    success: true,
    message: "Hotel booking API is running",
  });
});

app.use("/api", routes);
app.use(notFound);
app.use(errorHandler);

module.exports = app;
