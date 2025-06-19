const fs = require('fs');
const path = require('path');

// Read the input file
const inputPath = './100DDtemp.txt';
const outputPath = './output.csv';
const fileContent = fs.readFileSync(inputPath, 'utf-8');

// Split into lines
const lines = fileContent.split(/\r?\n/);

// Process lines
let currentSpeaker = null;
let currentText = [];
const rows = [];

for (const line of lines) {
  const speakerMatch = line.match(/^[-\s]*([A-Z]+):\s*$/);
  if (speakerMatch) {
    // Save previous speaker's text block
    if (currentSpeaker && currentText.length > 0) {
      rows.push({ speaker: currentSpeaker, text: currentText.join(' ') });
    }
    // Set new speaker
    currentSpeaker = speakerMatch[1];
    currentText = [];
  } else if (line.trim()) {
    currentText.push(line.trim());
  }
}

// Save the last block
if (currentSpeaker && currentText.length > 0) {
  rows.push({ speaker: currentSpeaker, text: currentText.join(' ') });
}

// Write CSV
const csvLines = ['speaker,text'];
for (const { speaker, text } of rows) {
  const safeText = text.replace(/"/g, '""'); // escape quotes
  csvLines.push(`${speaker},"${safeText}"`);
}

fs.writeFileSync(outputPath, csvLines.join('\n'), 'utf-8');

console.log(`✅ CSV written to ${outputPath}`);
