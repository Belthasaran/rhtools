const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('rhtools', {
    version: '0.1.0'
});


