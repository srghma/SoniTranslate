// const fs = require("fs");
// const path = require("path");
// const { glob } = require("glob");
// const { mkdirp } = require("mkdirp");
// const StealthPlugin = require("puppeteer-extra-plugin-stealth");
// const puppeteerExtra = require("puppeteer-extra");
// const AdblockerPlugin = require("puppeteer-extra-plugin-adblocker");

import * as fs from "fs";
import path from "path";
import glob from "glob";
import mkdirp from "mkdirp";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import puppeteerExtra from "puppeteer-extra";
import AdblockerPlugin from "puppeteer-extra-plugin-adblocker";

puppeteerExtra.use(StealthPlugin());
// puppeteerExtra.use(AdblockerPlugin());

var downloadsDir = path.join(process.env.HOME, "Downloads");

var srts = await glob(`${downloadsDir}/**/*.srt`);

function checkFileExists(file) {
  return fs.promises
    .access(file, fs.constants.F_OK)
    .then(() => true)
    .catch(() => false);
}

var userDataDir = "./.puppeteer_userdata";
await mkdirp(userDataDir);

var browser = await puppeteerExtra.launch({
  headless: false, // Set to true to run without a visible browser window
  executablePath:
    "/nix/store/75bwm98xdd421vi1av16qwcxz64dgsw9-system-path/bin/google-chrome-stable", // Specify the path to the Chromium executable
  // userDataDir, // Store session data in this directory
  defaultViewport: null, // Set a custom viewport size
  slowMo: 20,
  args: [
    "--disable-infobars", // Disable the "Chrome is being controlled by automated software" message
    "--disable-notifications", // Disable browser notifications
    "--disable-extensions", // Disable browser extensions
    "--disable-dev-shm-usage", // Disable /dev/shm usage to prevent crashes in some environments
    "--disable-background-networking", // Disable background network requests
    "--disable-default-apps", // Disable default apps
    "--disable-sync", // Disable browser sync
    "--disable-translate", // Disable page translation
    // '--no-sandbox', // Disable sandboxing for more compatibility (only use this in secure environments)
    "--disable-web-security", // https://vladislav-puzyrev.github.io/vk-spammer-online/
    "--disable-blink-features=AutomationControlled",
    "--disable-automation",
  ],
});

var page = await browser.newPage(); // Open a new page

srts = [
  "/home/srghma/Downloads/Kindergarten Cop (1990)/Kindergarten.Cop.1990.720p.BluRay.x264.YIFY.srt",
];

srts = srts.map((srt) => ({
  srt,
  outputPathInDownloads:
    "/home/srghma/Downloads/" + path.basename(srt).replace(/\.srt$/, ".km.srt"),
  outputPath: srt.replace(/\.srt$/, ".km.srt"),
}));

for (const { srt, outputPathInDownloads, outputPath } of srts) {
  if (!(await checkFileExists(srt))) {
    throw new Error(`File not found ${srt}`);
  }
  if (await checkFileExists(outputPathInDownloads)) {
    console.log(`${outputPathInDownloads} exists`);
  }
  if (await checkFileExists(outputPath)) {
    console.log(`${outputPath} exists`);
  }
}

for (const { srt, outputPathInDownloads, outputPath } of srts) {
  // var srt = srts[2];
  if (!(await checkFileExists(srt))) {
    throw new Error(`File not found ${srt}`);
  }

  // use puppeteer to translate srt to khmer using google translate

  // await page.goto(`file://${srt}`);

  await page.goto(`https://www.syedgakbar.com/projects/dst`);

  await page.waitForSelector("#srtFileDropZone", { visible: true });

  var dropZone = await page.$(".dz-hidden-input");
  dropZone.uploadFile(srt);

  // wait until see "#transWidgets" (text should be visible)
  do {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    await page.waitForSelector("#transWidgets", { visible: true });
    var elem = await page.$("#transWidgets");
    var text = await page.evaluate((el) => el.textContent, elem);
  } while (!text.includes("Translator"));
  await new Promise((resolve) => setTimeout(resolve, 500));

  // prevent "Node is either not clickable or not an Element" when clicking of option inside of "select.goog-te-combo"
  await page.waitForSelector("select.goog-te-combo", { visible: true });

  // select in .goog-te-combo option with valud "kh"
  await page.select("select.goog-te-combo", "km");
  await new Promise((resolve) => setTimeout(resolve, 500));

  await page.waitForSelector("#btnTranslate", { visible: true });
  await page.click("#btnTranslate");

  // wait until see "All subtitles translated successfully" inside of ".col-sm-8"
  do {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    await page.waitForSelector(".col-sm-8", { visible: true });
    var elem = await page.$(".col-sm-8");
    var text = await page.evaluate((el) => el.textContent, elem);
  } while (!text.includes("All subtitles translated successfully"));
  // wait until a file was downloaded
  await new Promise((resolve) => setTimeout(resolve, 500));

  await page.waitForSelector("#btnSaveAsSubtitle", { visible: true });
  await page.click("#btnSaveAsSubtitle");

  // check output file exists using fs.promises.access(outputPath);
  do {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    var outputPathExists = await checkFileExists(outputPathInDownloads);
  } while (!outputPathExists);

  console.log(`${outputPathExists} is downloaded`);

  // move from outputPathInDownloads to outputPath
  await fs.promises.rename(outputPathInDownloads, outputPath);
  console.log(`${outputPath} is created`);
}

await browser.close();
