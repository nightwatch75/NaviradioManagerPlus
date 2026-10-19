# Curated genre list (radio-browser tags are free text). The app merges it
# with the most used tags returned by the API (/json/tags).
_RAW = """
60s, 70s, 80s, 90s, 2000s, acid jazz, acoustic, adult contemporary, afrobeat, afrobeats, alternative,
alternative country, alternative rock, ambient, americana, anime, arabic, audiophile, ballads, bachata,
bebop, bhangra, big band, big beat, blues, bluegrass, bollywood, bossa nova, breakbeat, breakcore, britpop,
brazilian, bubblegum, calypso, carnatic, celtic, chanson, chillout, chillwave, christian, christmas,
cinematic, classic hits, classic rock, classical, club, comedy, contemporary christian, country, cumbia,
dance, dancehall, dark ambient, death metal, deep house, deep techno, disco, doo-wop, downtempo,
drum and bass, dream pop, drone, dub, dubstep, easy listening, edm, electro, electro swing, electronic,
electropop, emo, ethnic, eurodance, europop, experimental, fado, flamenco, folk, folk metal, folk rock,
forro, freestyle, funk, funk carioca, fusion, future bass, gangsta rap, garage, garage rock, glam rock,
gospel, goth, gothic, grunge, hard house, hard rock, hardcore, hardcore punk, hardstyle, heavy metal,
hi-nrg, hindustani, hip hop, hip-hop, house, hyperpop, idm, indie, indie folk, indie pop, indie rock,
industrial, instrumental, italian pop, italo disco, j-pop, j-rock, jazz, jazz fusion, jazz rap, jungle,
k-pop, karaoke, kids, krautrock, latin, latin jazz, latin pop, lo-fi, lofi hip hop, lounge, manele,
mariachi, math rock, melodic death metal, merengue, metal, metalcore, minimal, mizrahi, motown, musical,
neo soul, new age, new romantic, new wave, noise, nu disco, nu jazz, nu metal, oldies, opera,
orchestral, pagode, polka, pop, pop rock, post-punk, post-rock, power metal, power pop, progressive,
progressive house, progressive metal, progressive rock, psychedelic, psytrance, pub rock, punk, punk rock, r&b, ragga, rai,
rap, reggae, reggaeton, retro, rhythm and blues, rock, rock and roll, rockabilly, romantic, salsa,
samba, schlager, sertanejo, shoegaze, ska, slow rock, smooth jazz, soft rock, soul, soundtrack,
southern rock, space rock, speed metal, stoner rock, surf rock, swing, symphonic metal, synthpop,
synthwave, tango, tech house, techno, thrash metal, trance, trap, tropical, trip hop, turkish, twee,
uk garage, urban, vaporwave, variety, video game music, vocal jazz, western swing, world, world music, zouk,
news, talk, politics, health, religion, islamic, quran, bible, education, history, science, culture,
traffic, weather, sports, local, community, university, public radio, top 40, hits, charts, mix
"""
GENRES = sorted({g.strip() for g in _RAW.replace("\n", " ").split(",") if g.strip()})
