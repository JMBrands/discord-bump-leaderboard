import disnake
import os
import json
import requests
import time
from tqdm import tqdm

token = os.environ["TOKEN"]
client = disnake.Client()
gateway = "https://discord.com/api/v10"


@client.event
async def on_ready():
    channel_id = int(input("Channel id for leaderboard: "))
    channel: disnake.TextChannel = await client.fetch_channel(channel_id)
    message: disnake.Message = await channel.send("# Bumpers Leaderboard")

    bump_channel_id = int(input("Bumping Channel id: "))
    # bump_channel: disnake.TextChannel = await client.fetch_channel(bump_channel_id)
    leaderboard = {"channel": channel_id, "message": message.id,
                   "streak": {"last": "0", "count": 0}}
    req = requests.get(f"{gateway}/channels/{bump_channel_id}/messages?limit=100",
                       headers={"Authorization": f"Bot {token}"})
    res = req.json()
    while len(res) == 100:
        res = req.json()
        for message in tqdm(res):
            if "interaction" in message.keys() and message["interaction"]["name"] == "bump":
                inter = message["interaction"]
                if inter["user"]["id"] in leaderboard:
                    leaderboard[inter["user"]["id"]] += 1
                else:
                    leaderboard[inter["user"]["id"]] = 1

                if leaderboard["streak"]["last"] == inter["user"]["id"]:
                    leaderboard["streak"]["count"] += 1
                else:
                    leaderboard["streak"]["last"] = inter["user"]["id"]
                    leaderboard["streak"]["count"] = 1
        req = requests.get(f"{gateway}/channels/{bump_channel_id}/messages?limit=100&before={
                           message['id']}", headers={"Authorization": f"Bot {token}"})
        time.sleep(0.3)
        embeds: list[disnake.Embed] = []
        keys: list = list(leaderboard.keys())
        for key in ["channel", "message", "streak"]:
            keys.remove(key)

        sorted = []
        for i in range(len(keys)):
            highest = keys[0]
            for key in keys:
                if leaderboard[key] > leaderboard[highest]:
                    highest = key
            sorted.append(highest)
            keys.remove(highest)

        i = 1
        last_key = None
        for key in sorted:
            user: disnake.Member = await channel.guild.getch_member(int(key))
            name = user.nick
            if not name:
                name = user.global_name
            if not name:
                name = user.name
            if last_key != None and leaderboard[last_key] == leaderboard[key]:
                i -= 1

            embeds.append(disnake.Embed(title=f" # {i}",
                                        description=f"{leaderboard[key]} bump{'' if leaderboard[key] == 1 else 's'}{
                f' (streak of {leaderboard["streak"]["count"]})'if key == leaderboard["streak"]["last"] else ''}",
                color=user.accent_color),
            )

            avatar = user.avatar
            if not avatar:
                avatar = user.default_avatar
            embeds[-1].set_author(name=name, icon_url=avatar)

            last_key = key
            i += 1

        await (await (await client.fetch_channel(leaderboard["channel"])).fetch_message(leaderboard["message"])).edit(content="# Bumpers Leaderboard",
                                                                                                                      embeds=embeds)

    with open(input("Leaderboard file: "), "w") as file:
        json.dump(leaderboard, file)
    print("done!")


if __name__ == "__main__":
    client.run(token)
