const gplay = require('google-play-scraper');

gplay.search({
    term: process.argv[2],
    num: 1
})
.then((data) => console.log(JSON.stringify(data)))
.catch(console.error);


