const express = require("express");
require("dotenv").config();
const bodyParser = require("body-parser");
const fs = require("fs");
const { createAppAuth } = require("@octokit/auth-app");
const { Octokit } = require("@octokit/core");

const app = express();
app.use(bodyParser.json());

// App credentials
const APP_ID = process.env.APP_ID;
;
const PRIVATE_KEY = process.env.PRIVATE_KEY.replace(/\\n/g, "\n");
 // Make sure the file name matches your key file

// Helper to get Octokit for a specific installation
async function getInstallationOctokit(owner) {
  const auth = createAppAuth({
    appId: APP_ID,
    privateKey: PRIVATE_KEY,
  });

  const appAuth = await auth({ type: "app" });

  const tempOctokit = new Octokit({ auth: appAuth.token });
  const installations = await tempOctokit.request("GET /app/installations");

  const installation = installations.data.find(inst => inst.account.login === owner);
  if (!installation) {
    throw new Error(`GitHub App not installed on account: ${owner}`);
  }

  const installationAuth = await auth({
    type: "installation",
    installationId: installation.id,
  });

  return new Octokit({ auth: installationAuth.token });
}

// Route to receive test cases and push to repo
app.post("/push_test_cases", async (req, res) => {
  const { owner, repo, testCases, path = "tests/generated.test.js" } = req.body;

  if (!owner || !repo || !testCases) {
    return res.status(400).json({ error: "Missing required fields: owner, repo, testCases" });
  }

  try {
    const octokit = await getInstallationOctokit(owner);
    const content = Buffer.from(testCases).toString("base64");

    let sha;
    try {
      const file = await octokit.request("GET /repos/{owner}/{repo}/contents/{path}", {
        owner,
        repo,
        path,
      });
      sha = file.data.sha;
    } catch (err) {
      if (err.status !== 404) throw err;
    }

    await octokit.request("PUT /repos/{owner}/{repo}/contents/{path}", {
      owner,
      repo,
      path,
      message: "Add generated test cases",
      content,
      sha,
    });

    res.json({ success: true, message: "✅ Test cases pushed to repo!" });
  } catch (error) {
    console.error("Error pushing test cases:", error.message);
    res.status(500).json({ error: "❌ Failed to push test cases." });
  }
});

// Root route
app.get("/", (req, res) => {
  res.send("🚀 GitHub Test Case Pusher is running!");
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});