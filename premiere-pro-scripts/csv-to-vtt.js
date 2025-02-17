import * as fs from "node:fs";
// import { exec } from "node:child_process";
// import * as path from "node:path";
// import glob from "glob";
// import srtParser2 from "srt-parser-2";
// import languageEncoding from "detect-file-encoding-and-language";
// import translator from "open-google-translator";
// import * as sqlite3 from "sqlite3";
// import { open } from "sqlite";
import csv from "csv-parser";

/////////////

const args = process.argv.slice(process.argv[0].endsWith("node") ? 2 : 1);

// Input and output file paths
const inputFile = args[0]; // Change this to your CSV filename
const outputFile = inputFile.replace(".csv", ".rt"); // Change this to your output file name

// Function to convert time format from "hh:mm:ss:ff" to "hh:mm:ss.mmm"
function convertTime(timecode) {
  // console.log("timecode", timecode);
  let [hh, mm, ss, ff] = timecode.split(":").map(Number);
  let milliseconds = Math.round((ff / 30) * 1000); // Assuming 30 fps
  return `${hh.toString().padStart(2, "0")}:${mm.toString().padStart(2, "0")}:${ss.toString().padStart(2, "0")}.${milliseconds.toString().padStart(3, "0")}`;
}

function mergeSpeakers(speakerName) {
  // Remove quotes and newlines from speaker name
  speakerName = speakerName.replace(/[\n"]/g, "");

  const map = {
    "Speaker 1": "srghma",
    "Speaker 2": "guest",
    "Speaker 4": "guest",
  };

  if (!map.hasOwnProperty(speakerName)) {
    console.error(`mergeSpeakers -> Unknown speaker name: ${speakerName}`);
    process.exit(1);
  }
  return map[speakerName];
}

function getColor(speakerName) {
  const map = {
    "Speaker 1": null,
    "Speaker 2": "#FFFF00", // Yellow
    "Speaker 4": "#FF0000", // Red
  };

  if (!map.hasOwnProperty(speakerName)) {
    console.error(`getColor -> Unknown speaker name: ${speakerName}`);
    process.exit(1);
  }
  return map[speakerName];
}

function colorizeText(text, color) {
  if (!color) {
    return text;
  }
  return `<font color="${color}">${text}</font>`;
}

function shouldMergeSubtitles(lastSubtitle, current) {
  return (
    lastSubtitle.speaker === current.speaker && !lastSubtitle.text.endsWith(".")
  );
}

function mergeSubtitles(subtitles, current) {
  const lastSubtitle = subtitles[subtitles.length - 1];

  if (subtitles.length > 0 && shouldMergeSubtitles(lastSubtitle, current)) {
    return [
      ...subtitles.slice(0, -1),
      {
        ...lastSubtitle,
        text: `${lastSubtitle.text} ${current.text}`,
        endTime: current.endTime,
      },
    ];
  }

  return [...subtitles, current];
}

function generateRTContent(subtitles) {
  const content = subtitles
    .map(({ speaker, startTime, endTime, text }) => {
      // return `${startTime} --> ${endTime}\n${colorizeText(text, getColor(speaker))}\n\n`;
      return `${startTime} --> ${endTime}\n${speaker}: ${text}\n\n`;
    })
    .join("");

  return content;
}

let rows = await new Promise((resolve, reject) => {
  const results = [];
  fs.createReadStream(inputFile, { encoding: "utf-8" })
    .pipe(
      csv({
        skipEmptyLines: true,
        trim: true,
      }),
    )
    .on("data", (row) => results.push(row))
    .on("end", () => resolve(results))
    .on("error", reject);
});

rows = rows.filter((row) => Object.keys(row).length > 0);
// console.log(rows[rows.length - 1]);

rows = rows.map((row) => ({
  speaker: row["Speaker Name"].trimStart("\n").replace(/^"|"$/g, ""),
  startTime: convertTime(row["Start Time"]),
  endTime: convertTime(row["End Time"]),
  text: row["Text"].trim(),
}));

rows = rows.map((row) => ({
  ...row,
  speaker: mergeSpeakers(row.speaker),
}));

const subtitles = rows.reduce(mergeSubtitles, []);

const rtContent = generateRTContent(subtitles);

await fs.promises.writeFile(outputFile, rtContent, "utf8");
console.log(`✅ RT file saved as ${outputFile}`);
