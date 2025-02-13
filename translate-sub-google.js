var fs = require('fs');
var path = require('path');
var translate = require('google-translate-api');
var archiver = require('archiver');

var dir = "/home/srghma/Downloads/The Bodyguard (1992)"
var inputFile = path.join(dir, 'en.srt');
var kmFile = path.join(dir, 'km.srt');
var mergedFile = path.join(dir, 'en-km.srt');
