# make sure you have the disnake & requests libraries installed via pip
import disnake
import os
import json
import requests

token = os.environ["TOKEN"]
client = disnake.Client()
gateway = "https://discord.com/api/v10"
leaderboardfile = "./leaderboard.json"
with open(leaderboardfile, "r") as file:
    leaderboard: dict = json.load(file)


@client.event
async def on_message(message: disnake.Message):
    req = requests.get(f"{gateway}/channels/{message.channel.id}/messages/{message.id}",
                       headers={"Authorization": "Bot " + token})
    res: dict = req.json()

    if "interaction" in res.keys():
        inter = res["interaction"]
        if inter["name"] == "bump":
            if str(inter["user"]["id"]) in leaderboard:
                leaderboard[inter["user"]["id"]] += 1
            else:
                leaderboard[inter["user"]["id"]] = 1

            if leaderboard["streak"]["last"] == inter["user"]["id"]:
                leaderboard["streak"]["count"] += 1
            else:
                leaderboard["streak"]["last"] = inter["user"]["id"]
                leaderboard["streak"]["count"] = 1

            with open(leaderboardfile, "w") as file:
                json.dump(leaderboard, file)
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
                user: disnake.Member = await message.guild.getch_member(int(key))
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
            # await message.channel.send(f"Thanks <@{inter["user"]["id"]}> for bumping!") # enable if you want a thank you message

if __name__ == "__main__":

    client.run(token)
