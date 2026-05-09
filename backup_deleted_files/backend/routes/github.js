import express from 'express';
const router = express.Router();
import { setTokens, clearTokens, isConnected, getToken, getUser } from '../services/tokenStore.js';

router.get('/status', (req, res) => {
  const connected = isConnected('github');
  const user = getUser('github');
  res.json({ connected, user: user ? { login: user.login } : null });
});

router.post('/connect', async (req, res) => {
  try {
    const { code } = req.body;
    
    if (!code) {
      return res.status(400).json({ error: 'Authorization code required' });
    }

    const mockToken = `gh_token_${Date.now()}`;
    const mockUser = { login: 'demo_user', id: 12345 };
    
    setTokens('github', mockToken, mockUser);
    
    res.json({ success: true, user: mockUser });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/disconnect', (req, res) => {
  clearTokens('github');
  res.json({ success: true });
});

router.get('/repos', async (req, res) => {
  try {
    if (!isConnected('github')) {
      return res.status(401).json({ error: 'Not connected to GitHub' });
    }

    const mockRepos = [
      { id: 1, name: 'my-project', description: 'A sample project', language: 'JavaScript' },
      { id: 2, name: 'api-server', description: 'REST API server', language: 'Node.js' },
      { id: 3, name: 'dashboard', description: 'Admin dashboard', language: 'React' }
    ];

    res.json(mockRepos);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/user', async (req, res) => {
  try {
    if (!isConnected('github')) {
      return res.status(401).json({ error: 'Not connected to GitHub' });
    }

    const user = getUser('github');
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

export default router;