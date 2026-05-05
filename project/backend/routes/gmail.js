const express = require('express');
const router = express.Router();
const { setTokens, clearTokens, isConnected } = require('../services/tokenStore');

router.get('/status', (req, res) => {
  const connected = isConnected('gmail');
  res.json({ connected });
});

router.post('/connect', async (req, res) => {
  try {
    const { code } = req.body;
    
    if (!code) {
      return res.status(400).json({ error: 'Authorization code required' });
    }

    const mockToken = `gmail_token_${Date.now()}`;
    setTokens('gmail', mockToken);
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/disconnect', (req, res) => {
  clearTokens('gmail');
  res.json({ success: true });
});

router.get('/emails', async (req, res) => {
  try {
    if (!isConnected('gmail')) {
      return res.status(401).json({ error: 'Not connected to Gmail' });
    }

    const mockEmails = [
      { id: 1, from: 'team@github.com', subject: 'Welcome to GitHub', date: '2024-01-15' },
      { id: 2, from: 'notifications@npmjs.com', subject: 'Package updates', date: '2024-01-14' },
      { id: 3, from: 'alerts@vercel.com', subject: 'Deployment completed', date: '2024-01-13' }
    ];

    res.json(mockEmails);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/send', async (req, res) => {
  try {
    if (!isConnected('gmail')) {
      return res.status(401).json({ error: 'Not connected to Gmail' });
    }

    const { to, subject, body } = req.body;
    
    res.json({ success: true, messageId: `msg_${Date.now()}` });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.get('/search', async (req, res) => {
  try {
    if (!isConnected('gmail')) {
      return res.status(401).json({ error: 'Not connected to Gmail' });
    }

    const { q } = req.query;
    
    res.json([]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;