require('dotenv').config();
const express = require('express');
const cors = require('cors');
const app = express();

const connectionsRouter = require('../routes/connections');
const githubRouter = require('../routes/github');
const gmailRouter = require('../routes/gmail');
const driveRouter = require('../routes/drive');

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

app.use('/connections', connectionsRouter);
app.use('/github', githubRouter);
app.use('/gmail', gmailRouter);
app.use('/drive', driveRouter);

app.use((err, req, res, next) => {
  console.error('Error:', err.message);
  res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});