const { app, BrowserWindow } = require('electron');
const path = require('path');

function createMainWindow() {
    const mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
        show: false,
    });

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    if (process.env.ELECTRON_START_URL) {
        mainWindow.loadURL(process.env.ELECTRON_START_URL);
    } else {
        const prodIndex = path.join(__dirname, 'renderer', 'dist', 'index.html');
        mainWindow.loadFile(prodIndex);
    }
}

app.whenReady().then(() => {
    createMainWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createMainWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});


