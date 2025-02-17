var fs = require("fs");
var path = require("path");
var { glob } = require("glob");
var { mkdirp } = require("mkdirp");
var { translateText, translateDocs } = require("puppeteer-google-translate");
var srtParser2 = require("srt-parser-2").default;
var languageEncoding = require("detect-file-encoding-and-language");
var parser = new srtParser2();
var translator = require("open-google-translator");

// import * as fs from "fs";
// import path from "path";
// import glob from "glob";
// import mkdirp from "mkdirp";
// import StealthPlugin from "puppeteer-extra-plugin-stealth";
// import puppeteerExtra from "puppeteer-extra";
// import srtParser2 from "srt-parser-2";

var downloadsDir = path.join(process.env.HOME, "Downloads");

var srts = await glob(`${downloadsDir}/**/*.srt`);

function checkFileExists(file) {
  return fs.promises
    .access(file, fs.constants.F_OK)
    .then(() => true)
    .catch(() => false);
}

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

srts = await Promise.all(
  srts.map(async ({ srt, outputPathInDownloads, outputPath }) => {
    const buffer = fs.readFileSync(srt);
    const charsetMatch = await languageEncoding(buffer);
    const { encoding, language } = charsetMatch;
    if (charsetMatch.confidence.encoding !== 1) {
      throw new Error(
        `not confidence.encoding: ${charsetMatch.confidence.encoding} for ${charsetMatch.encoding}`,
      );
    }
    if (charsetMatch.confidence.language !== 1) {
      throw new Error(
        `not confidence.language: ${charsetMatch.confidence.language} for ${charsetMatch.language}`,
      );
    }
    const srtString = buffer.toString(encoding);
    return { srt, srtString, outputPathInDownloads, outputPath };
  })
);

srts = srts.map((x) => {
  const { srt, srtString, outputPathInDownloads, outputPath } = x;
  const srt_array = parser.fromSrt(srtString);
  return { srt, srt_array, outputPathInDownloads, outputPath }
})

for (const { srt, srt_array, outputPathInDownloads, outputPath } of srts) {
  // var { srt, srt_array, outputPathInDownloads, outputPath } = srts[0];
  var srt_array_str = srt_array.map(x => x.text).filter(x => x.trim())
  var output = await translateDocs("/home/srghma/Downloads/Kindergarten Cop (1990)/Kindergarten.Cop.1990.720p.BluRay.x264.YIFY.txt", {
    from: 'en',
    to: 'km',
    timeout: 10000,
    headless: false,
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
  })

  // use puppeteer to translate srt to khmer using google translate

  // await page.goto(`file://${srt}`);

  await page.goto(`https://www.syedgakbar.com/projects/dst`);

  await page.waitForSelector("#srtFileDropZone");

  var dropZone = await page.$(".dz-hidden-input");
  dropZone.uploadFile(srt);

  // wait until see "#transWidgets" (text should be visible)
  do {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    var elem = await page.$("#transWidgets");
    var text = await page.evaluate((el) => el.textContent, elem);
  } while (!text.includes("Translator"));
  await new Promise((resolve) => setTimeout(resolve, 500));

  await page.waitForSelector("select.goog-te-combo");

  // prevent "Node is either not clickable or not an Element" when clicking of option inside of "select.goog-te-combo"
  // await page.select("select.goog-te-combo", "km");

  // select in .goog-te-combo option with valud "kh"
  await page.select("select.goog-te-combo", "km");
  await new Promise((resolve) => setTimeout(resolve, 500));

  await page.click("#btnTranslate");

  // wait until see "All subtitles translated successfully" inside of ".col-sm-8"
  do {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    var elem = await page.$(".col-sm-8");
    var text = await page.evaluate((el) => el.textContent, elem);
  } while (!text.includes("All subtitles translated successfully"));
  // wait until a file was downloaded
  await new Promise((resolve) => setTimeout(resolve, 500));

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
