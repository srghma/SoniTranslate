// const dle_root = "https://rezka.ag/";
// const cdnItemId = 75728;
// const cdnTranslatorId = 316;
// const cdnSeason = 1;
// const cdnEpisode = 1;
//
// try {
//   const response = await fetch(
//     `${dle_root}ajax/get_cdn_series/?t=${Date.now()}`,
//     {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify({
//         id: cdnItemId,
//         translator_id: cdnTranslatorId,
//         season: cdnSeason,
//         episode: cdnEpisode,
//         favs: "a737dede-57b3-4c84-8d25-73a331853a47",
//         action: "get_episodes",
//       }),
//     },
//   );
//
//   if (!response.ok) {
//     throw new Error("Network response was not ok");
//   }
//
//   const data = await response.json();
//   console.log(data);
//
//   const CDNPlayerInfo = {
//     streams: data.url,
//     default_quality: data.quality,
//     subtitle: data.subtitle,
//     subtitle_lns: data.subtitle_lns,
//     subtitle_def: data.subtitle_def,
//     thumbnails: data.thumbnails,
//   };
//
//   console.log(CDNPlayerInfo);
// } catch (error) {
//   console.error("Error fetching CDN data:", error);
// }
