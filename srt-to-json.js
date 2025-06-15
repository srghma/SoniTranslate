const path = require("path");
const fs = require("fs");
const subtitlesParser = require("subtitles-parser");
const R = require('ramda')
const translate = require('@iamtraction/google-translate');

var filmSubtitle = subtitlesParser.fromSrt(fs.readFileSync("/home/srghma/Downloads/[Russian] Animations of unseeable biology _ Drew Berry _ TED [DownSub.com].srt.txt", "utf8"), true);

var input2 = JSON.parse(fs.readFileSync("/tmp/zshyrUwU4.zsh", "utf8"));

// var input = fs.readFileSync("/home/srghma/projects/SoniTranslate/[Russian] Animations of unseeable biology _ Drew Berry _ TED [DownSub.com].srt.txt", "utf8").split('\n').filter(x => x)
var input = fs.readFileSync("./output-kh.txt", "utf8").split('\n').filter(x => x).map(x => R.last(x.split('|')).trim())

if (input.length !== input2.length) { throw new Error(`input.length ${input.length} !== filmSubtitle.length ${filmSubtitle.length}`) }


x = R.zipWith((x, newtext) => ({ ...x, text: newtext }), input2, input)
fs.writeFileSync(path.join(".", "output-kh.json"), JSON.stringify(x, null, 2));


// x = await translate(fs.readFileSync("./output.txt", "utf8"), { from: 'ru', to: 'km' })
// fs.writeFileSync(path.join(".", "output-kh.txt"), x.text);

// x = R.zipWith((x, y) => `${x.start} | ${x.text} | ${y}`, input2, input).join('\n')

// var output = dataMs.map((item) => {
//   return {
//     start: item.startTime / 1000,
//     text: item.text,
//     spearker: 1,
//   }
// });

// fs.writeFileSync(path.join(".", "output.txt"), x);
// fs.writeFileSync(path.join(".", "output.txt"), x);
