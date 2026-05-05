const express = require('express');
const router = express.Router();
const { getTokens, isConnected, getToken, getUser } = require('../services/tokenStore');
const { checkHealth } = require('../services/mcpClient');

router.get('/', (req, res) => {
  const tokens = getTokens();
  const connections = {
    github: { connected: tokens.github.connected, username: tokens.github.user?.login || null },
    gmail: { connected: tokens.gmail.connected },
    drive: { connected: tokens.drive.connected }
  };
  res.json(connections);
});

router.get('/health', async (req, res) => {
  const health = {};
  const apps = ['github', 'gmail', 'drive'];
  
  for (const app of apps) {
    health[app] = await checkHealth(app);
  }
  
  res.json(health);
});

module.exports = router;