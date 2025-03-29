// var fs = require("fs");
// var path = require("path");
// var { mkdirp } = require("mkdirp");
// var changeFileExtension = require("change-file-extension").default;
// var pathCompleteExtname = require('path-complete-extname')
// var translator = require("open-google-translator");

import * as fs from "fs";
import * as path from "path";
import mkdirp from "mkdirp";
import changeFileExtension from "change-file-extension";
import pathCompleteExtname from "path-complete-extname";

const args = process.argv.slice(process.argv[0].endsWith("node") ? 2 : 1).then((x) => x.filter(Boolean));

var [from, to, ...filePaths] = args;

filePaths.forEach((filePath) => {
  if (pathCompleteExtname(filePath).toLowerCase() == ".info.json") {
    return;
  }
  throw new Error(`Wrong file ${filePath}`);
});

filePaths = filePaths.map((filePath) => ({
  filePath,
  outputPath: changeFileExtension(filePath, `.${to}.${pathCompleteExtname(filePath)}`),
}));

for (const { filePath, outputPath } of srts) {
  if (!(await checkFileExists(filePath))) {
    throw new Error(`File not found ${filePath}`);
  }
  if (await checkFileExists(outputPath)) {
    console.log(`${outputPath} exists`);
  }
}
