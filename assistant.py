import os, discord, asyncio, datetime, dateutil.parser, requests, re, json, youtube_dl, enum, io
from discord.ext import commands
from dateutil import tz

settings = {
    "AUTH_TOKEN": os.environ["DISCORD_TOKEN"],
    "channels": [],
    "tc_general": 455719906244034561,
    "vc_general": 455719906244034563,
    "tc_music": 456588364775161857,
    "vc_music": 456588393401548821
}

assistant = commands.Bot(command_prefix=commands.when_mentioned_or("/"), description="I'm not your assistant!")

class Songs(enum.Enum):
    WOTW_JP = "Weight of the World／壊レタ世界ノ歌",
    WOTW_YORHA = "Weight of the World／the End of YoRHa",
    FAREWELL = "Steins;Gate OST - Farewell",
    CREEP = "Creep (feat. Ember Island)",
    FUBUKI = "Fubuki (KanColle)",
    CROSSING_FIELD = "Crossing Field",
    FIRESTORM = "Firestorm ft. Sara Diamond (Abandoned Remix)",
    THIS_GAME = "This Game",
    SHIRUSHI = "Shirushi"

class AudioPlayer(discord.AudioSource):
    def __init__(self, song):
        super().__init__()

        print("Playing {}".format(song))

        if song == Songs.WOTW_JP:
            self.stream_url = "http://download1127.mediafire.com/ud0e7ym47hfg/35g8mkw4p1r0f2v/WotW.wav"
        elif song == Songs.WOTW_YORHA:
            self.stream_url = "http://download1217.mediafire.com/ub5br4m2e4vg/fr3wi0ox1urcn33/WotWYorha.wav"
        elif song == Songs.FAREWELL:
            self.stream_url = "http://download770.mediafire.com/73a4yf685ing/k9ci2ts8buha21u/Farewell.wav"
        elif song == Songs.CREEP:
            self.stream_url = "http://download1519.mediafire.com/bx8j0kl997eg/fh1r5867w3mst51/Creep.wav"
        elif song == Songs.FUBUKI:
            self.stream_url = "http://download2182.mediafire.com/f3134vq7icyg/db80ukro11yk1gz/Fubuki.wav"
        elif song == Songs.CROSSING_FIELD:
            self.stream_url = "http://download1971.mediafire.com/ej0ti7oozv5g/xyldlulkjrbqv8p/CrossingField.wav"
        elif song == Songs.FIRESTORM:
            self.stream_url = "http://download1454.mediafire.com/d7yvzsppq6ug/qrxgf48ijqakmd1/Firestorm.wav"
        elif song == Songs.THIS_GAME:
            self.stream_url = "http://download1773.mediafire.com/jlqkfnr6g7bg/1kznb17kby1b1f2/ThisGame.wav"
        elif song == Songs.SHIRUSHI:
            self.stream_url = "http://download1608.mediafire.com/to7t1oloyebg/m68url1w0fotidu/Shirushi.wav"

        self.stream = requests.get(self.stream_url, stream=True)
        self.iterator = self.stream.iter_content(chunk_size=3840)

    def read(self):
        chunk = next(self.iterator)
        if chunk:
            return chunk

    def cleanup(self):
        self.stream.close()

async def check_updates():
    await assistant.wait_until_ready()
    while not assistant.is_closed():
        print("Reloading channel list")

        settings["channels"] = json.loads(requests.get(os.environ["CHANNEL_LIST_URL"]).text)

        print("Got {} different channels".format(len(settings["channels"])))

        for ch in settings["channels"]:
            channel = assistant.get_channel(ch["id"])

            print("  Checking channel {}".format(channel))

            history = await channel.history(limit=1).flatten()

            prev = 1

            if len(history) == 1:
                try:
                    prev = re.search(r"https:\/\/danbooru.donmai.us\/posts\/(\d+)", history[0].embeds[0].url).group(1)
                except IndexError:
                    print ("      IndexError when parsing regex for string \"{}\"".format(history[0].embeds[0].url))
                    continue

            print("    Got previous post id: {}".format(prev))

            try:
                count = json.loads(requests.get("https://danbooru.donmai.us/counts/posts.json?tags={}+id:>{}".format(ch["tag"], prev)).text)["counts"]["posts"]
            except json.decoder.JSONDecodeError:
                print("  JSONDecodeError: Danbooru might be down")
                break

            print("    Discovered {} new posts".format(count))

            if count == 0:
                print("    Continuing...")
                continue

            posts = []
            baseurl = "https://danbooru.donmai.us/posts.json?{}"

            # https://stackoverflow.com/a/17511341
            pagecount = -(-count // 200)

            for p in range(pagecount):
                data = "tags={}+id:>{}&page={}&limit=200".format(ch["tag"], prev, p + 1)
                print("      Loading page {} of {}\n      Data: {}".format(p + 1, pagecount, data))
                posts.extend(json.loads(requests.get(baseurl.format(data)).text))

            ids = []
            for p in posts:
                ids.append(p["id"])

            ids = sorted(list(set(ids)), key=int)

            print("    Got {} new posts, outputting...".format(len(ids)))

            index = 0
            for i in ids:
                if index % 50 == 0:
                    print("      {} out of {}".format(index, len(ids)))

                index += 1

                await channel.send("`[{}]`\n https://danbooru.donmai.us/posts/{}".format(datetime.datetime.utcnow().replace(tzinfo=tz.tzutc()), i))

            print("      {} out of {}".format(len(ids), len(ids)))

        slept = 0
        while slept < 3600:
            print("Sleeping for {} more seconds".format(3600 - slept))
            slept += 60
            await asyncio.sleep(60)

@assistant.event
async def on_ready():
    print("--------------")
    print(assistant.user)
    print("--------------")

@assistant.command()
async def tsun(ctx, msg: str = ""):
    if not list(filter(lambda c: c["id"] == ctx.message.channel.id, settings["channels"])):
        await ctx.send("Message: " + msg)

@assistant.command()
async def nullpo(ctx):
    if not list(filter(lambda c: c["id"] == ctx.message.channel.id, settings["channels"])):
        await ctx.send("Gah!")

@assistant.command(aliases=["Christina", "Kurisutina", "kurisutina"])
async def christina(ctx):
    if not list(filter(lambda c: c["id"] == ctx.message.channel.id, settings["channels"])):
        await ctx.send("There's no -tina!")

@assistant.command()
async def notice(ctx):
    await ctx.message.delete()

    if ctx.message.channel.id == settings["tc_music"]:
        channel = assistant.get_channel(settings["vc_music"])

        global vc

        vc = await channel.connect()

@assistant.command()
async def begone(ctx):
    await ctx.message.delete()

    if ctx.message.channel.id == settings["tc_music"]:
        global vc

        await vc.disconnect()

@assistant.command()
async def volume(ctx, volume: float = -1):
    await ctx.message.delete()

    if not "player" in globals():
        return

    global player

    if ctx.message.channel.id == settings["tc_music"]:
        if 0 < volume <= 2:
            player.volume = volume

            await ctx.send("Changed volume to {}".format(volume))
        else:
            await ctx.send("Volume must be a `float` between 0 and 2")

@assistant.command()
async def pause(ctx):
    await ctx.message.delete()

    if not "vc" in globals():
        return

    global vc

    if vc.is_connected() and not vc.is_paused():
        print("Pausing playback")

        vc.pause()

@assistant.command()
async def resume(ctx):
    await ctx.message.delete()

    if not "vc" in globals():
        return

    global vc

    if vc.is_connected() and vc.is_paused():
        print("Resuming playback")

        vc.resume()

@assistant.command()
async def stop(ctx):
    await ctx.message.delete()

    if not "vc" in globals():
        return

    global vc

    if vc.is_connected():
        print("Stopping playback")

        vc.stop()

@assistant.command()
async def play(ctx, song: str = ""):
    await ctx.message.delete()
    
    if not "vc" in globals():
        return

    global vc

    if vc.is_connected():
        if ctx.message.channel.id == settings["tc_music"]:
            selected = None

            song = song.lower()

            if song == "wotw_jp":
                selected = Songs.WOTW_JP
            elif song == "wotw_yorha":
                selected = Songs.WOTW_YORHA
            elif song == "farewell":
                selected = Songs.FAREWELL
            elif song == "creep":
                selected = Songs.CREEP
            elif song == "fubuki":
                selected = Songs.FUBUKI
            elif song == "crossing_field":
                selected = Songs.CROSSING_FIELD
            elif song == "firestorm":
                selected = Songs.FIRESTORM
            elif song == "this_game":
                selected = Songs.THIS_GAME
            elif song == "shirushi":
                selected = Songs.SHIRUSHI

            await ctx.send("Playing `{}`".format(selected))

            global player
            player = discord.PCMVolumeTransformer(AudioPlayer(selected))
            
            vc.play(player, after=lambda err: print(err) if err else print("Done playing"))

@assistant.command()
async def assistant_help(ctx):
    await ctx.message.delete()

    if ctx.message.channel.id == settings["tc_music"]:
        await ctx.send("""
Commands:

    `/notice` - connect `Assistant` to the voice channel

    `/begone` - disconnect `Assistant`

    `/volume <float>` - sets the volume (values 0-2)

    `/pause` - pauses playback

    `/resume` - resumes playback

    `/stop` - stops playback
    
    `/play <song>` - plays a song (case insensitive)


Songs:

    `WotW_JP` - Weight of the World／壊レタ世界ノ歌"

    `WotW_YoRHa` - Weight of the World／the End of YoRHa

    `Farewell` - Steins;Gate OST - Farewell

    `Creep` - Creep (feat. Ember Island)

    `Fubuki` - Fubuki (KanColle)

    `Crossing_Field` - Crossing Field

    `Firestorm` - Firestorm ft. Sara Diamond (Abandoned Remix)

    `This_Game` - This Game

    `Shirushi` - Shirushi`
        """)

assistant.loop.create_task(check_updates())
assistant.run(settings["AUTH_TOKEN"])