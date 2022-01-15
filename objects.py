import discord
import random
import pytweet
from discord import ButtonStyle
from discord.ext import commands
from discord.ui import View, Button, Select
from pytweet import Tweet
from typing import Optional, Union
from twitter import TwitterUser


def to_keycap(c):
    return "\N{KEYCAP TEN}" if c == 10 else str(c) + "\u20e3"


def format_mentioned(text):
    if len(text) <= 0:
        return "*User doesnt provide a bio*"

    original_split = text.split(" ")
    bio = (
        text.replace("@", "[@")
        .replace("#", "[#")
        .replace("PyTweet", "[PyTweet")
        .replace("pytweet", "[pytweet")
    )
    split_bio = bio.split(" ")
    complete = ""
    for num, word in enumerate(split_bio):
        before_word = ""
        if "." in word and "t.co" not in word:
            before_word += "."
            word = word.replace(".", "")

        if "[" in word:
            if "#" in word:
                value = original_split[num].replace("#", "").replace("\n", "")
                complete += f" {word}](https://twitter.com/hashtag/{value}?src=hashtag_click){before_word}"
            elif "@" in word:
                value = original_split[num].replace("@", "").replace("\n", "")
                complete += f" {word}](https://twitter.com/{value}){before_word}"
            elif "PyTweet" in word or "pytweet" in word:  # ;)
                complete += f" {word}](https://github.com/PyTweet/PyTweet){before_word}"

        else:
            complete += " " + word

    return complete if len(complete) <= 4096 else text


def get_badges(ctx, user) -> str:
    text = ""
    badges = ["✅ ", "🔒 ", "⚒️ "]
    if user.verified:
        text += badges[0]
    if user.protected:
        text += badges[1]
    if user.id in ctx.bot.twitter_dev_ids:
        text += badges[2]
    return text


class DisplayModels:
    def __init__(self, bot):
        self.bot = bot

    async def display_user(
        self,
        ctx: commands.Context,
        user: Union[discord.User, discord.Member, TwitterUser],
    ):
        _tweets = []

        async def callback(inter):
            if inter.user.id != ctx.author.id:
                await inter.response.send_message("This is not for you", ephemeral=True)
                return

            tweet_id = inter.data["values"][0]
            await self.display_tweet(
                ctx,
                _tweets[int(tweet_id)] if tweet_id.isdigit() else tweet_id,
                inter,
                replace_user_with=user,
            )

        async def timeout():
            for button in buttons:
                button.disabled = True

            select.disabled = True
            try:
                if isinstance(message, discord.Interaction):
                    await message.edit_original_message(view=view)
                else:
                    await message.edit(view=view)
            except Exception as e:
                raise e

        async def follow(inter):
            if inter.user.id != ctx.author.id:
                await inter.response.send_message("This is not for you", ephemeral=True)
                return

            if user.id == int(
                ctx.bot.db[str(ctx.author.id)]["token"].split("-")[0]
            ):  # not all data have "user_id" key, we use the access token that include the id.
                buttons[0].disabled = True
                try:
                    if isinstance(message, discord.Interaction):
                        await message.edit_original_message(view=view)
                    else:
                        await message.edit(view=view)
                except Exception as e:
                    raise e
                await ctx.send("You cannot follow yourself!")
                return

            user.follow()
            label = buttons[0].label.split(" ")
            buttons[0].label = str(int(label[0]) + 1) + " " + label[1]
            buttons[0].disabled = True
            try:
                if isinstance(message, discord.Interaction):
                    await message.edit_original_message(view=view)
                else:
                    await message.edit(view=view)
            except Exception as e:
                raise e
            await inter.response.send_message(
                f"Followed {user.username}!", ephemeral=True
            )

        options = []
        keycaps = [to_keycap(x) for x in range(1, 6)]
        view = View(timeout=200.0)

        buttons = [
            Button(
                label=f"{user.follower_count} Followers",
                emoji="🤗",
                style=ButtonStyle.blurple,
            ),
            Button(
                label=f"{user.following_count} Following",
                emoji="🤗",
                style=ButtonStyle.blurple,
            ),
            Button(
                label=f"{user.tweet_count} Tweets",
                emoji="<:retweet:914877560142299167>",
                style=ButtonStyle.blurple,
            ),
        ]
        tweets = user.fetch_timelines(max_results=5, exclude="replies,retweets")
        buttons[0].callback = follow

        for num, tweet in enumerate(tweets):
            if user.protected:
                options.append("Protected")
                break

            else:
                _tweets.append(tweet)
                options.append(
                    discord.SelectOption(
                        label=f"({tweet.created_at.strftime('%d/%m/%Y')}) {tweet.text[:25]}{'...' if len(tweet.text) > 25 else ''}",
                        value=str(num),
                        description="(click to see full result)"
                        if len(tweet.text) > 25
                        else "",
                        emoji=keycaps[num],
                        default=False,
                    )
                )

        unknown_tweet = "None" if not tweets and not user.protected else ""
        placeholder = "(Recent User Timelines)"
        if user.protected:
            placeholder = "(User Is Protected!)"
        elif not user.protected and unknown_tweet == "None":
            placeholder = "(Unknown Timelines)"

        if options and not unknown_tweet == "None":
            options = options  # For understanding, purely unnecessarily
        elif user.protected:
            options = [
                discord.SelectOption(
                    label="???",
                    value="protected",
                    description="Cannot fetch user timelines...\n User is protected!",
                    default=False,
                )
            ]
        else:
            options = [
                discord.SelectOption(
                    label="???",
                    value="None",
                    description="User have no tweets timelines!",
                    default=False,
                )
            ]

        select = Select(placeholder=placeholder, options=options)
        select.callback = callback

        for button in buttons:
            view.add_item(button)
        view.add_item(select)
        bio = format_mentioned(user.bio)

        badges = get_badges(ctx, user)
        em = (
            discord.Embed(
                title=user.name + " " + badges,
                url=user.profile_link,
                description=f"{bio}\n\n:link: {user.link if len(user.link) > 0 else '*This user doesnt provide a link*'} • <:compas:879722735377469461> {user.location if len(user.location) > 0 else '*This user doesnt provide a location*'}",
                color=discord.Color.blue(),
            )
            .set_author(
                name=user.username + f"({user.id})",
                icon_url=user.profile_url,
                url=user.profile_link,
            )
            .set_footer(
                text=f"Created Time: {user.created_at.strftime('%d/%m/%Y')}",
                icon_url=user.profile_url,
            )
        )

        view.on_timeout = timeout

        message = await ctx.send(embed=em, view=view)

    async def display_tweet(
        self,
        ctx: Optional[commands.Context] = None,
        tweet: Optional[Tweet] = None,
        method: Optional[Union[commands.Context, discord.Interaction]] = None,
        *,
        client=None,
        replace_user_with=None,
    ):
        user = tweet.author if isinstance(tweet, Tweet) else None
        if not client:
            client = await self.bot.get_user(ctx.author.id, ctx)
        if not user:
            user = replace_user_with
        if not method:
            method = ctx
        if not isinstance(tweet, Tweet):
            if isinstance(method, discord.Interaction):
                await method.response.send_message(
                    f"Unknown tweet! {'Cannot fetch timelines, user is protected!' if tweet == 'protected' else 'User have no tweets timelines!'}",
                    ephemeral=True,
                )

            elif isinstance(method, commands.Context):
                await method.send(
                    f"Unknown tweet! {'Cannot fetch timelines, user is protected!' if tweet == 'protected' else 'User have no tweets timelines!'}"
                )
            return

        async def like(inter):
            if inter.user.id != ctx.author.id:
                await inter.response.send_message("This is not for you", ephemeral=True)
                return

            tweet.like()
            await inter.response.send_message(
                f"{client.twitter_account.username} Liked the tweet!", ephemeral=True
            )
            label = buttons[0].label.split(" ")
            buttons[0].label = str(int(label[0]) + 1) + " " + label[1]
            buttons[0].disabled = True
            try:
                if isinstance(message, discord.Interaction):
                    await message.edit_original_message(view=view)
                else:
                    await message.edit(view=view)
            except Exception as e:
                raise e

        async def retweet(inter):
            if inter.user.id != ctx.author.id:
                await inter.response.send_message("This is not for you", ephemeral=True)
                return

            tweet.retweet()
            await inter.response.send_message(
                f"{client.twitter_account.username} retweeted the tweet!",
                ephemeral=True,
            )
            label = buttons[1].label.split(" ")
            buttons[1].label = str(int(label[0]) + 1) + " " + label[1]
            buttons[1].disabled = True
            try:
                if isinstance(message, discord.Interaction):
                    await message.edit_original_message(view=view)
                else:
                    await message.edit(view=view)
            except Exception as e:
                raise e

        async def reply(inter):
            if inter.user.id != ctx.author.id:
                await inter.response.send_message("This is not for you", ephemeral=True)
                return

            def check(msg):
                return msg.author.id == inter.user.id

            await ctx.send("Send your reply message!")
            message = await self.bot.wait_for("message", check=check, timeout=60)
            tweet.reply(message.content)
            await inter.response.send_message(
                f"{user.username} replied to the tweet!", ephemeral=True
            )
            await ctx.send("Reply completed!")

        async def images(inter):
            if inter.user.id != ctx.author.id:
                await inter.response.send_message("This is not for you", ephemeral=True)
                return

            if not medias:
                await inter.response.send_message("No media available for this tweet!")
                return

            if len(medias) > 1:
                embed = em.copy()
                img = random.choice(medias)
                embed.set_image(
                    url=img.url
                    if img.type == pytweet.MediaType.photo
                    else img.preview_image_url
                )
                try:
                    if isinstance(message, discord.Interaction):
                        await message.edit_original_message(embed=embed)
                    else:
                        await message.edit(embed=embed)
                except Exception as e:
                    raise e
            else:
                await inter.response.send_message(
                    "No more images available!", ephemeral=True
                )

        async def timeout():
            for button in buttons:
                button.disabled = True

            await message.edit(view=view)

        callbacks = [like, retweet, images]  # TODO add reply and fix reply callback.

        if not ctx.channel.is_nsfw() and tweet.sensitive:
            await method.response.send_message(
                "This tweet has a sensitive content and might end up as nsfw, gore, and disturbing content. Use this command in nsfw channel!",
                ephemeral=True,
            ) if isinstance(method, discord.Interaction) else await method.send(
                "This tweet has a sensitive content and might end up as nsfw, gore, and other disturbing contents. Use this command in nsfw channel!",
                ephemeral=True,
            )
            return

        try:
            link = tweet.link
        except (TypeError, AttributeError):
            link = f"https://twitter.com/{user.username.replace('@', '', 1)}/status/{str(tweet.id)}"

        text = format_mentioned(tweet.text)
        medias = tweet.media
        em = (
            discord.Embed(
                title=user.name + " " + get_badges(ctx, user),
                url=link,
                description=text,
                color=discord.Color.blue()
                if not tweet.sensitive
                else discord.Color.red(),
            )
            .set_author(
                name=user.username + f"({user.id})",
                icon_url=user.profile_url,
                url=user.profile_link,
            )
            .set_footer(
                text=f"Conversation ID: {tweet.conversation_id}",
                icon_url=user.profile_url,
            )
            .add_field(name="Tweet Date", value=tweet.created_at.strftime("%d/%m/%Y"))
            .add_field(name="Reply Setting", value=tweet.raw_reply_setting)
            .add_field(
                name="Source",
                value=f"[{tweet.source}](https://help.twitter.com/en/using-twitter/how-to-tweet#source-labels)",
            )
        )

        if tweet.media:
            img = random.choice(medias)
            em.set_image(
                url=img.url
                if img.type == pytweet.MediaType.photo
                else img.preview_image_url
            )

        buttons = [
            Button(
                label=f"{tweet.like_count} Like",
                emoji="👍",
                style=discord.ButtonStyle.blurple,
            ),
            Button(
                label=f"{tweet.retweet_count} Retweet",
                emoji="<:retweet:914877560142299167>",
                style=discord.ButtonStyle.blurple,
            ),
            Button(
                label=f"{len(medias)} Media" if medias else "No Media Available",
                emoji="<:images:879722735817850890>",
                style=discord.ButtonStyle.green,
                row=2,
            ),
            Button(
                label=f"{tweet.reply_count} Reply",
                emoji="🗨️",
                style=discord.ButtonStyle.blurple,
            ),
        ]
        view = View(timeout=200.0)
        view.on_timeout = timeout

        for num, callback in enumerate(callbacks):
            buttons[num].callback = callback

        for button in buttons:
            view.add_item(button)

        if isinstance(method, discord.Interaction):
            message = await method.response.send_message(
                content="You know you can do: `e!tweet <tweet_id>` to see other tweet's info!\nlooks like this tweet has a poll, mind checking that out with `e!poll <tweet_id>`?"
                if tweet.id == 1465231032760684548 and tweet.poll
                else "You know you can do: `e!tweet <tweet_id>` to see other tweet's info!"
                if tweet.id == 1465231032760684548
                else "looks like this tweet has a poll, mind checking that out with `e!poll <tweet_id>`?"
                if tweet.poll
                else "",
                embed=em,
                view=view,
                ephemeral=True,
            )

        else:
            if tweet.id == 1465231032760684548:
                await method.send(
                    "You know you can do: `e!tweet <tweet_id>` to see other tweet's info!"
                )

            if tweet.poll:
                await method.send(
                    "looks like this tweet has a poll, mind checking that out with `e!poll <tweet_id>`?"
                )

            message = await method.send(embed=em, view=view)
