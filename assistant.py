import os, discord, asyncio, datetime, dateutil.parser, requests, re, json
from discord.ext import commands
from dateutil import tz

settings = {
    "AUTH_TOKEN": os.environ["DISCORD_TOKEN"],
    "category": int(os.environ["ASSISTANT_CATEGORY"]),
    "channels": []
}

assistant = commands.Bot(command_prefix="/", description="I'm not your assistant!")

async def check_updates():
    await assistant.wait_until_ready()
    if not assistant.is_closed():
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

            count = json.loads(requests.get("https://danbooru.donmai.us/counts/posts.json?tags={}+id:>{}".format(ch["tag"], prev)).text)["counts"]["posts"]

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


       #await asyncio.sleep(43200)


@assistant.event
async def on_ready():
    print("--------------")
    print(assistant.user)
    print("--------------")

    #for c in assistant.get_all_channels():
    #    if type(c) == discord.channel.CategoryChannel and c.id == settings["category"]:
    #        settings["channels"] = c.channels

    #print("Got {} channels under category {}".format(len(settings["channels"]), settings["category"]))

    print("Binding to category {}".format(settings["category"]))


@assistant.command()
async def tsun(ctx, msg: str = ""):
    if ctx.message.channel not in settings["channels"]:
        await ctx.send("Message: " + msg)

@assistant.command()
async def nullpo(ctx):
    if ctx.message.channel not in settings["channels"]:
        await ctx.send("Gah!")

@assistant.command()
async def christina(ctx):
    if ctx.message.channel not in settings["channels"]:
        await ctx.send("There's no -tina!")

@assistant.command()
async def Christina(ctx):
    if ctx.message.channel not in settings["channels"]:
        await ctx.send("There's no -tina!")

@assistant.command()
async def kurisutina(ctx):
    if ctx.message.channel not in settings["channels"]:
        await ctx.send("There's no -tina!")

@assistant.command()
async def Kurisutina(ctx):
    if ctx.message.channel not in settings["channels"]:
        await ctx.send("There's no -tina!")

assistant.loop.create_task(check_updates())
assistant.run(settings["AUTH_TOKEN"])