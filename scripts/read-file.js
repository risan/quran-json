const fs = require("fs");
const util = require("util");

const fsRead = util.promisify(fs.readFile);

const readFile = path => fsRead(`tanzil/${path}`, "utf8");

module.exports = readFile;
