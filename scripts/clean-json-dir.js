/* eslint import/no-extraneous-dependencies: "off" */
const rimraf = require("rimraf");

const cleanJsonDir = () =>
  new Promise((resolve, reject) =>
    rimraf("json", err => (err ? reject(err) : resolve()))
  );

module.exports = cleanJsonDir;
