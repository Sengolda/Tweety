import discord
import difflib
from discord.ext import commands


class CustomHelpCommand(commands.HelpCommand):
    @property
    def ctx(self):
        return self.context

    def get_ending_note(self, category: bool):
        return f"Use e!{self.invoked_with} [{'Category' if category else 'command'}] for more info on {'all commands' if category else 'the command'}"

    def get_command_signature(self, command):
        return command.signature or " "

    async def send_bot_help(self, mapping):
        cog_description = {
            "RTFM": "Command to look at pytweet library!",
            "Twitter": "Commands for using certain twitter action!",
            "Owner": "Commands that can only be use by the bot's owner",
        }

        emojis = {"RTFM": "🔍", "Twitter": "<:pytweet:922818933919199272>", "Owner": "👑"}
        em = discord.Embed(
            title="HelpCommand",
            description="Hello there, I'm Tweety! A bot with twitter client functions inside of discord!\n\n**Select A Category:**",
            color=discord.Color.from_rgb(136, 223, 251),
        )
        for cog, cmd in mapping.items():
            att = getattr(cog, "qualified_name", "No Category")
            if (
                att != "No Category"
                and att.lower() != "jishaku"
                and att.lower() != "terces"
            ):
                all_commands = cog.get_commands()
                em.add_field(
                    name=f"{emojis[att]} {att} [{len(all_commands)}]",
                    value=cog_description[att],
                    inline=False,
                )

        em.set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar.url)
        em.set_footer(
            text=self.get_ending_note(True), icon_url=self.ctx.author.avatar.url
        )
        channel = self.get_destination()
        await channel.send(embed=em)

    async def send_cog_help(self, cog):
        em = discord.Embed(
            title=f"{cog.qualified_name}'s commands",
            description="",
            color=discord.Color.from_rgb(136, 223, 251),
        )

        for cms in cog.get_commands():
            com = cms.name
            em.description += f"`{com}`, "

        em.set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar.url)
        em.set_footer(
            text=self.get_ending_note(False), icon_url=self.ctx.author.avatar.url
        )
        channel = self.get_destination()
        await channel.send(embed=em)

    async def send_command_help(self, command):
        channel = self.get_destination()
        desc = command.description
        aliases = command.aliases

        if aliases == []:
            aliases.append("This command dont have aliases")

        em = (
            discord.Embed(
                title=command.name,
                description=desc,
                color=discord.Color.from_rgb(136, 223, 251),
            )
            .add_field(
                name="Syntax",
                value=f"e!{command.qualified_name} {self.get_command_signature(command)}",
                inline=True,
            )
            .add_field(
                name="Aliases",
                value=", ".join(x for x in aliases if not x.startswith(" ")),
                inline=True,
            )
            .set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar.url)
            .set_footer(
                text=f"Requested by {self.ctx.author}",
                icon_url=self.ctx.author.avatar.url,
            )
        )

        await channel.send(embed=em)

    async def command_not_found(self, error):
        channel = self.get_destination()
        category = difflib.get_close_matches(
            error.title(), ["Owner", "RTFM", "Twitter"]
        )

        if category:
            embed = (
                discord.Embed(
                    title=f"No Category called '{error}' ",
                    description=f"Did you mean `{', '.join(category)}`",
                    color=discord.Color.red(),
                )
                .set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar.url)
                .set_footer(
                    text=f"Use e!{self.invoked_with} for more info about all commands",
                    icon_url=self.ctx.author.avatar.url,
                )
            )
        else:
            embed = (
                discord.Embed(
                    title=f"No Command called '{error}' ",
                    description=f"Did you mean `.....`",
                    color=discord.Color.red(),
                )
                .set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar.url)
                .set_footer(
                    text=f"Use e!{self.invoked_with} for more info about all commands",
                    icon_url=self.ctx.author.avatar.url,
                )
            )

        await channel.send(embed=embed)
