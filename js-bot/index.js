const express = require("express");
const bodyParser = require("body-parser");

const app = express();
const port = 3000; // Use your desired port

// GitHub Webhook Secret (for security)
const webhookSecret = "supersecret123";  // GitHub provides this when setting up the webhook

// Middleware to parse JSON bodies
app.use(bodyParser.json());

// Webhook handler
app.post("/webhook", (req, res) => {
  const payload = req.body;
  const event = req.headers["x-github-event"];
  const signature = req.headers["x-hub-signature"];

  // Verify the signature (for security)
  // Here, you should verify that the payload is coming from GitHub using your secret

  console.log(`Received event: ${event}`);
  console.log("Payload:", JSON.stringify(payload, null, 2));

  // You can add conditions to log specific events like push, pull request, etc.
  if (event === "push") {
    console.log("Push event detected!");
  }

  // Send a success response back to GitHub
  res.status(200).send("Webhook received!");
});

// Start the server
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
