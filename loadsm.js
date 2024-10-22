const fs = require('fs');
const UrlBase64 = require('urlsafe-base64');

const path = require('path');
const process = require('process');
const crypto = require('crypto');
const zlib = require('zlib'); // For decompression (LZMA would require a specific library)
const { promisify } = require('util');
const decompress = promisify(zlib.unzip); // Simplified example using unzip
const { parse } = require('json5'); // To handle JSON with comments or non-standard syntax

const fernet = require('fernet');
const lzma = require('lzma-native');
const { Buffer } = require('buffer');


// Dummy function for key retrieval, replace with actual logic
function rhmd_key(filename) {
    // Implement your logic to get the key
    return 'JtSYvgCpAX4Hz_J63g-5dmDKbJp_Dl2GnKL_yuhoEck=';
}


// Dummy function for path prefix, replace with actual implementation
function getPathPrefix() {
    // Implement your logic to determine the path prefix
    if (process.env.RHTOOLS_PATH) {
        return process.env.RHTOOLS_PATH;
    }
    return ''; // Replace with your actual path prefix logic
}

function rhmd_path() {
    const pathPrefix = getPathPrefix();
    const files = [
        'RHMD_FILE',
        'rhmd.dat',
        'rhmd_dist.dat',
        'rhmd_sample2.dat',
        'rhmd_sample.dat'
    ];

    // Check if 'RHMD_FILE' environment variable is set
    if (process.env.RHMD_FILE) {
        return process.env.RHMD_FILE;
    }

    // Check for the existence of each file in order
    for (const file of files.slice(1)) {
        const filePath = path.join(pathPrefix, file);
        if (fs.existsSync(filePath)) {
            return filePath;
        }
    }

    // If 'rhmd_dist.dat' file is not found, throw an error
    const fallbackPath = path.join(pathPrefix, 'rhmd_dist.dat');
    if (!fs.existsSync(fallbackPath)) {
        throw new Error('No rhmd DAT file found. Did you forget to extract rhtools-sampledata-20xx.tar.gz?');
    }

    return fallbackPath;
}


// Function to decode base64 and decrypt using Fernet-like encryption
async function decryptFernet(encryptedData, key) {
    // Fernet is not directly available in Node.js, so you might need to use a library or implement it
    // This is a placeholder implementation
	// frnsecret = new fernet.Secret(frnkeyS)

    //const decipher = crypto.createDecipheriv('aes-256-cbc', Buffer.from(key, 'base64'), Buffer.alloc(16, 0)); // Adjust mode and key
    //let decrypted = Buffer.concat([decipher.update(encryptedData), decipher.final()]);
    //console.log(`new fernet.Secret ${key}`)
    //console.log(`encryptedData = ${encryptedData}`)
	//
	//
    frnsecret = new fernet.Secret(key);
	//console.log("X:"+encryptedData);
    //encryptedData = UrlBase64.decode( encryptedData ).toString();
    token = new fernet.Token({secret: frnsecret, ttl: 0, token: encryptedData })

    //console.log("DECODE:" + encryptedData);
    //console.log(token.decode(encryptedData));
    return token.decode();
}

async function getHacklistData(filename) {
    if (!filename) {
        filename = rhmd_path();
    }

    //const key = Buffer.from(rhmd_key(filename), 'ascii').toString(); //.toString('base64');
    var key = rhmd_key(filename).toString();
    var fileContent = fs.readFileSync(filename, 'utf8');
    let hacklist;

    if (fileContent[0] === '*') {
	fileContent = fileContent.substring(1);


        // Use LZMA decompression or equivalent
        //const decrypted = await decryptFernet(Buffer.from(fileContent.substring(1), 'base64'), key);
	const decrypted = await decryptFernet(fileContent, key);
        const decompressed = await decompress(decrypted);
        hacklist = JSON.parse(decompressed.toString('utf8'));
    } else if (fileContent[0] === '[' || fileContent[0] === '{') {
        if (fileContent[0] === '{') {
            fileContent = '[' + fileContent + ']';
        }
        hacklist = JSON.parse(fileContent); // Handle file if not encoded
    } else {
        hacklist = JSON.parse(Buffer.from(fileContent, 'base64').toString('utf8'));
    }

    return hacklist;
}



///
//
//
//


//const fs = require('fs');
//const fernet = require('fernet');
//const lzma = require('lzma-native');
//const { Buffer } = require('buffer');

// Function to initialize Fernet
function getFernetInstance(key) {
    return new fernet.Token({
        secret: Buffer.from(key, 'base64'),
        ttl: 0 // Set to 0 for no expiration
    });
}

async function getGenListData(filename, fernetKey) {
    // Read the file contents
    const data = fs.readFileSync(filename, 'utf8');
    let hacklist = null;

    if (data[0] === '*') {
        // Decrypt and decompress the data
        const fernetInstance = getFernetInstance(fernetKey);
        const decryptedData = fernetInstance.decrypt(Buffer.from(data, 'utf8')).toString('utf8');
        const decompressedData = await lzma.decompress(Buffer.from(decryptedData, 'base64'));
        hacklist = JSON.parse(decompressedData.toString('utf8'));
    } else if (data[0] === '[' || data[0] === '{') {
        if (data[0] === '{') {
            // Wrap single JSON object in array brackets
            const wrappedData = '[' + data + ']';
            hacklist = JSON.parse(wrappedData);
        } else {
            // Directly parse the JSON array
            hacklist = JSON.parse(data);
        }
    } else {
        // Base64 decode and parse
        const base64Data = Buffer.from(data, 'base64').toString('utf8');
        hacklist = JSON.parse(base64Data);
    }

    return hacklist;
}

module.exports = {
    getGenListData,
    getHacklistData
};


var hld = getHacklistData();







