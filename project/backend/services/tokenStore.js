let tokens = {
  github: { connected: false, token: null, user: null },
  gmail: { connected: false, token: null },
  drive: { connected: false, token: null }
};

const getTokens = () => tokens;

const setTokens = (app, token, user = null) => {
  if (tokens[app]) {
    tokens[app].connected = true;
    tokens[app].token = token;
    if (user) tokens[app].user = user;
  }
};

const clearTokens = (app) => {
  if (tokens[app]) {
    tokens[app].connected = false;
    tokens[app].token = null;
    tokens[app].user = null;
  }
};

const isConnected = (app) => {
  return tokens[app] && tokens[app].connected;
};

const getToken = (app) => {
  return tokens[app] ? tokens[app].token : null;
};

const getUser = (app) => {
  return tokens[app] ? tokens[app].user : null;
};

module.exports = {
  getTokens,
  setTokens,
  clearTokens,
  isConnected,
  getToken,
  getUser
};