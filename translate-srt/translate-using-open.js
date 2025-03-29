// var fs = require("fs");
// var path = require("path");
// var { glob } = require("glob");
// var { mkdirp } = require("mkdirp");
// var { translateText, translateDocs } = require("puppeteer-google-translate");
// var srtParser2 = require("srt-parser-2").default;
// var languageEncoding = require("detect-file-encoding-and-language");
// var translator = require("open-google-translator");
// var Keyv = require("keyv").default;

import * as fs from "node:fs";
import { exec } from "node:child_process";
import * as path from "node:path";
import glob from "glob";
import srtParser2 from "srt-parser-2";
import languageEncoding from "detect-file-encoding-and-language";
import translator from "open-google-translator";
import * as sqlite3 from "sqlite3";

async function checkFileExists(file) {
  try {
    await fs.promises.access(file, fs.constants.F_OK);
    return true;
  } catch {
    return false;
  }
}
/////////////

const parser = new srtParser2();
// const downloadsDir = path.join(process.env.HOME, "Downloads");

const args = process.argv.slice(process.argv[0].endsWith("node") ? 2 : 1);

let srts = await Promise.all(
  args.map(async (filePath) => {
    if (filePath.match(/\.(mp4|mkv|avi|mov|wmv|flv|webm)$/i)) {
      const enSrtFile = filePath.replace(/\.[^.]+$/, ".en.srt");
      if (await checkFileExists(enSrtFile)) {
        console.log(`found srt file at ${enSrtFile}`);
        return enSrtFile;
      }

      const srtFile = filePath.replace(/\.[^.]+$/, ".srt");
      if (await checkFileExists(srtFile)) {
        console.log(`found srt file at ${srtFile}`);
        return srtFile;
      }

      console.log(`Trying ffmpeg -i "${filePath}" -map "0:s:0" "${srtFile}"`);

      await new Promise((resolve, reject) => {
        exec(`ffmpeg -i "${filePath}" -map "0:s:0" "${srtFile}"`, (error) => {
          if (error) reject(error);
          else resolve();
        });
      });
      return srtFile;
    }

    if (filePath.endsWith(".srt")) {
      return filePath;
    }

    throw new Error(`Cannot parse ${filePath}`);
  }),
).then((files) => files.filter(Boolean));

// let srts = await glob(`${downloadsDir}/**/*.srt`);

// srts = [
//   "/home/srghma/Downloads/Kindergarten Cop (1990)/Kindergarten.Cop.1990.720p.BluRay.x264.YIFY.srt",
// ];

srts = srts.map((srt) => ({
  srt,
  // outputPathInDownloads: "/home/srghma/Downloads/" + path.basename(srt).replace(/\.srt$/, ".km.srt"),
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
    if (charsetMatch.confidence.encoding !== 1) {
      console.log("charsetMatch:", charsetMatch);
      throw new Error(
        `${srt} -> low confidence.encoding: ${charsetMatch.confidence.encoding} for ${charsetMatch.encoding}`,
      );
    }
    if (charsetMatch.confidence.language !== 1) {
      console.log("charsetMatch:", charsetMatch);
      console.log(
        `${srt} -> low confidence.language: ${charsetMatch.confidence.language} for ${charsetMatch.language}`,
      );
    }
    let srtString = null;
    try {
      srtString = buffer.toString(charsetMatch.encoding);
    } catch (error) {
      console.log("Error converting buffer with detected encoding:", error);
      console.log("charsetMatch:", charsetMatch);
      // Fallback to UTF-8 if encoding fails
      srtString = buffer.toString("utf8");
      // Test that string is valid utf8 by attempting to re-encode
      const testEncode = Buffer.from(srtString, "utf8").toString("utf8");
      if (testEncode !== srtString) {
        throw new Error("Failed to convert file to UTF-8");
      }
    }
    return { srt, srtString, outputPathInDownloads, outputPath };
  }),
);

srts = srts.map((x) => {
  const { srt, srtString, outputPathInDownloads, outputPath } = x;
  const strDataArray = parser.fromSrt(srtString);
  return { srt, strDataArray, outputPathInDownloads, outputPath };
});


for (const { srt, strDataArray, outputPath } of srts) {
  console.log(`processing ${srt}`);
  // const { srt, strDataArray, outputPathInDownloads, outputPath } = srts[0];
  const output = await translateSrt({
    strDataArray,
    fromLanguage: "en",
    toLanguage: "km",
  });

  const outputWithMergedText = output.map((data) => ({
    ...data,
    text: `${data.text}\n<font color="yellow">${data.translation}</font>`,
  }));

  const srt_string = parser.toSrt(outputWithMergedText);

  fs.writeFileSync(outputPath, srt_string);

  console.log(`${outputPath} is created`);
}
