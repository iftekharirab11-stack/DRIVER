import express from 'express';
const router = express.Router();
import { getTokens, isConnected, getToken, getUser } from '../services/tokenStore.js';
import { checkHealth } from '../services/mcpClient.js';

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

export default router;