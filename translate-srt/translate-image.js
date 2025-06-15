var fs = require("fs");
var path = require("path");
var { mkdirp } = require("mkdirp");
var changeFileExtension = require("change-file-extension").default;
var which = require('which')
var { chromium } = require("playwright-extra")
var StealthPlugin = require('puppeteer-extra-plugin-stealth')

import * as fs from "fs";
import * as path from "path";
import mkdirp from "mkdirp";
import changeFileExtension from "change-file-extension";
import { chromium } from "playwright";
import StealthPlugin from 'puppeteer-extra-plugin-stealth'

// Add the plugin to playwright (any number of plugins can be added)
chromium.use(StealthPlugin())

function checkFileExists(file) {
  return fs.promises
    .access(file, fs.constants.F_OK)
    .then(() => true)
    .catch(() => false);
}

const args = process.argv.slice(process.argv[0].endsWith("node") ? 2 : 1).then((x) => x.filter(Boolean));

var [from, to, ...filePaths] = args;

filePaths.forEach((filePath) => {
  if (
    [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"].includes(
      path.extname(filePath).toLowerCase(),
    )
  ) {
    return;
  }
  throw new Error(`Wrong file ${filePath}`);
});

filePaths = filePaths.map((filePath) => ({
  filePath,
  outputPath: changeFileExtension(filePath, `.${to}.${path.extname(filePath)}`),
}));

for (const { filePath, outputPath } of srts) {
  if (!(await checkFileExists(filePath))) {
    throw new Error(`File not found ${filePath}`);
  }
  if (await checkFileExists(outputPath)) {
    console.log(`${outputPath} exists`);
  }
}

// var browser = await chromium.launchPersistentContext(
//   "/home/srghma/.config/google-chrome",
//   {
//     headless: false,
//     executablePath: which.sync("google-chrome-stable"),
//     slowMo: 20,
//   },
// );

var browser = await chromium.connectOverCDP('http://localhost:4444')
var page = await browser.newPage()
var from = "ru"
var to = "en"
var file = "/home/srghma/Downloads/nevzorov/thumbnail.jpg"
await page.goto(`https://translate.google.com/?sl=${from}&tl=${to}&op=images`)

await page.locator('.caTGn input[type="file"]', { state: 'attached' }).setInputFiles(file);

await browser.close();
