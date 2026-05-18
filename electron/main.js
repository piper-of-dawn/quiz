const { app, BrowserWindow, shell } = require('electron');
const appUrlConfig = require('./app-url.json');

const appUrl = process.env.APP_URL || appUrlConfig.url;

if (!appUrl) {
  throw new Error('APP_URL is required. Build with APP_URL=https://your-deployed-app.example');
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 900,
    minWidth: 960,
    minHeight: 680,
    title: 'MCQ Quiz',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  win.loadURL(appUrl);
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
