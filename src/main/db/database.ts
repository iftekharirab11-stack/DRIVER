import Database from 'better-sqlite3';
import path from 'path';
import { runMigrations } from './migrations';

// Determine database path: prefer Electron's app.getPath('userData'), fallback to local .data
function getDbPath(): string {
  try {
    // Electron environment
    const { app } = require('electron');
    const userDataPath = app.getPath('userData');
    return path.join(userDataPath, 'driver.db');
  } catch {
    // Fallback: local .data directory (for dev / standalone)
    const fallbackDir = path.join(process.cwd(), '.data');
    return path.join(fallbackDir, 'driver.db');
  }
}

const dbPath = getDbPath();
const db = new Database(dbPath);

// Execute migrations once on module load
runMigrations(db);

export default db;
