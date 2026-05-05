const axios = require('axios');
const { getToken } = require('./tokenStore');

const MCP_SERVERS = {
  github: 'http://localhost:3001',
  gmail: 'http://localhost:3002',
  drive: 'http://localhost:3003'
};

const callTool = async (app, action, payload = {}) => {
  const baseUrl = MCP_SERVERS[app];
  if (!baseUrl) {
    throw new Error(`Unknown app: ${app}`);
  }

  const token = getToken(app);
  if (!token) {
    throw new Error(`Not connected to ${app}`);
  }

  try {
    const response = await axios.post(`${baseUrl}/tools/${app}/${action}`, {
      ...payload,
      token
    }, {
      timeout: 10000
    });
    return response.data;
  } catch (error) {
    throw new Error(`MCP tool call failed: ${error.message}`);
  }
};

const checkHealth = async (app) => {
  const baseUrl = MCP_SERVERS[app];
  if (!baseUrl) return { status: 'offline' };

  try {
    await axios.get(`${baseUrl}/health`, { timeout: 3000 });
    return { status: 'healthy' };
  } catch (error) {
    return { status: 'offline' };
  }
};

const getGithubRepos = async () => {
  return callTool('github', 'listRepos');
};

const getGithubUser = async () => {
  return callTool('github', 'getUser');
};

const getEmails = async () => {
  return callTool('gmail', 'listEmails');
};

const getDriveFiles = async () => {
  return callTool('drive', 'listFiles');
};

module.exports = {
  callTool,
  checkHealth,
  getGithubRepos,
  getGithubUser,
  getEmails,
  getDriveFiles,
  MCP_SERVERS
};