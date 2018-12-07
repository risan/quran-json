/* eslint import/no-extraneous-dependencies: "off" */
const writeToFile = require("write-to-file");

const writeJson = (data, path) =>
  Promise.all([
    writeToFile(`json/${path}`, JSON.stringify(data)),
    writeToFile(
      `json/${path.replace(/\.json$/i, ".pretty.json")}`,
      JSON.stringify(data, null, 2)
    )
  ]);

module.exports = writeJson;
