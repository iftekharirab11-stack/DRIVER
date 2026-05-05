const express = require('express');
const router = express.Router();
const { setTokens, clearTokens, isConnected } = require('../services/tokenStore');

router.get('/status', (req, res) => {
  const connected = isConnected('drive');
  res.json({ connected });
});

router.post('/connect', async (req, res) => {
  try {
    const { code } = req.body;
    
    if (!code) {
      return res.status(400).json({ error: 'Authorization code required' });
    }

    const mockToken = `drive_token_${Date.now()}`;
    setTokens('drive', mockToken);
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.post('/disconnect', (req, res) => {
  clearTokens('drive');
  res.json({ success: true });
});

router.get('/files', async (req, res) => {
  try {
    if (!isConnected('drive')) {
      return res.status(401).json({ error: 'Not connected to Google Drive' });
    }

    const mockFiles = [
      { id: 1, name: 'project-plan.docx', type: 'document', size: '2.4 MB' },
      { id: 2, name: 'budget.xlsx', type: 'spreadsheet', size: '1.1 MB' },
      { id: 3, name: 'presentation.pptx', type: 'presentation', size: '5.2 MB' }
    ];

    res.json(mockFiles);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

router.delete('/files/:id', async (req, res) => {
  try {
    if (!isConnected('drive')) {
      return res.status(401).json({ error: 'Not connected to Google Drive' });
    }

    const { id } = req.params;
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;