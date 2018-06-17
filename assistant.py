import os, discord, asyncio, datetime, dateutil.parser, requests, re, json, youtube_dl, enum, io
from discord.ext import commands
from dateutil import tz

settings = {
    "AUTH_TOKEN": os.environ["DISCORD_TOKEN"],
    "server": int(os.environ["MAIN_SERVER"]),
    "assistant_category": int(os.environ["CHANNELS_CATEGORY"]),
    "admins": list(map(int, os.environ["ADMINS"].split(" "))),
    "requests": int(os.environ["REQUESTS_ID"]),
    "tc_general": 455719906244034561,
    "vc_general": 455719906244034563,
    "tc_music": 456588364775161857,
    "vc_music": 456588393401548821
}

session = {
    "force_refresh": False,
    "slept": 0
}

assistant = commands.Bot(command_prefix=commands.when_mentioned_or("/"), description="I'm not your assistant!")

async def check_updates():
    await assistant.wait_until_ready()
    while not assistant.is_closed():
        print("Rediscovering channels")

        category = assistant.get_channel(settings["assistant_category"])

        channels = []

        for c in category.channels:
            if c.id != settings["requests"]:
                channels.append(c)

        print("Got {} different channels".format(len(channels)))

        for channel in channels:
            tag = channel.topic.strip()

            print("  Checking tag {}".format(tag))

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
                count = json.loads(requests.get("https://danbooru.donmai.us/counts/posts.json?tags={}+id:>{}".format(tag, prev)).text)["counts"]["posts"]
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
                data = "tags={}+id:>{}&page={}&limit=200".format(tag, prev, p + 1)
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

        session["slept"] = 0
        while session["slept"] < 3600:
            if session["slept"] % 60 == 0:
                print("Sleeping for {} more seconds".format(3600 - session["slept"]))

            if session["force_refresh"]:
                session["force_refresh"] = False
                break

            session["slept"] += 15
            await asyncio.sleep(15)

@assistant.event
async def on_ready():
    print("--------------")
    print(assistant.user)
    print("--------------")

@assistant.command()
async def add(ctx, tag: str = ""):
    if ctx.message.channel.id == settings["requests"]:
        if ctx.message.author.id not in settings["admins"]:
            print("Denying add request for {}".format(ctx.message.author.id))

            await ctx.send("Insufficient permissions")
        else:
            if not tag:
                await ctx.send("No tag present")
            else:
                print("Attempting to add tag {}".format(tag))

                count = -1

                try:
                    count = json.loads(requests.get("https://danbooru.donmai.us/counts/posts.json?tags={}".format(tag)).text)["counts"]["posts"]
                except json.decoder.JSONDecodeError:
                    print("  JSONDecodeError: Danbooru might be down")
                    await ctx.send("JSONDecodeError: Danbooru might be down")

                if count <= 0:
                    await ctx.send("No posts under tag")
                    print("  Empty tag \"{}\"".format(tag))
                else:
                    print("  Creating text channel for \"{}\"".format(tag))

                    server = assistant.get_guild(settings["server"])

                    sanitise = ["'", "(", ")", "\\", "/", ":"]

                    name = tag

                    for char in sanitise:
                        name = name.replace(char, "")

                    category = assistant.get_channel(settings["assistant_category"])

                    new_channel = await server.create_text_channel(name, category=category)

                    channels = []

                    for c in category.channels:
                        if c.id != settings["requests"]:
                            channels.append(c.name)

                    channels.append(name)

                    channels.sort()

                    index = channels.index(name) + 1

                    await new_channel.edit(topic=tag)
                    await new_channel.edit(nsfw=True)
                    await new_channel.edit(position=index)

                    print("    Created text channel \"{}\" at index {}".format(name, index))

                    await ctx.send("Channel \"{}\" created".format(name))

@assistant.command()
async def force_refresh(ctx):
    if ctx.message.channel.id == settings["requests"]:
        if ctx.message.author.id not in settings["admins"]:
            print("Denying force_refresh request for {}".format(ctx.message.author.id))

            await ctx.send("Insufficient permissions")
        else:
            print("Forcing refresh with {} seconds left".format(3600 - session["slept"]))
            
            session["force_refresh"] = True

            await ctx.send("Refreshing as soon as possible...")

@assistant.command()
async def poll(ctx):
    if ctx.message.channel.id == settings["requests"]:
        await ctx.send("Time to next update: {} seconds".format(3600 - session["slept"]))

@assistant.command()
async def tsun(ctx, msg: str = ""):
    if ctx.message.channel.category_id != settings["assistant_category"]:
        await ctx.send("Message: " + msg)

@assistant.command()
async def nullpo(ctx):
    if ctx.message.channel.category_id != settings["assistant_category"]:
        await ctx.send("Gah!")

@assistant.command(aliases=["Christina", "Kurisutina", "kurisutina"])
async def christina(ctx):
    if ctx.message.channel.category_id != settings["assistant_category"]:
        await ctx.send("There's no -tina!")

assistant.loop.create_task(check_updates())
assistant.run(settings["AUTH_TOKEN"])