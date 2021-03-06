from asyncio import CancelledError
from libs import Macro, Paginate
from discord import Permissions, Color
from discord.ext import commands
from discord.utils import oauth_url
from libs.Tools import CustomPermissionError, Workers
from random import randrange


class Helper:
    def __init__(self, ctx, message):
        self.paginator = Paginate.Paginated(bot = ctx.bot,
                                            message = message,
                                            member = ctx.author,
                                            react_map = {
                                                "\U000025c0": self.prev,
                                                "\U000025b6": self.next,
                                                "\U000023f9": self.stop
                                            },
                                            on_start = self.edit_message)

        self.ignored = {"ErrorHandler"}
        self.ctx = ctx
        self.message = message
        self.size = 3
        self.index = 0
        self.cogs = [c for c in ctx.bot.cogs.keys() if c not in self.ignored]
        self.total = len(self.cogs)

    async def generate_help(self):
        help_items = {}
        current = self.cogs[self.index]
        current_commands = self.ctx.bot.get_cog(current).get_commands()
        for command in current_commands:
            if isinstance(command, commands.Group):
                for sub_com in command.commands:
                    docstring = sub_com.help if sub_com.help else "No docstring"
                    help_items[command.name + " " + sub_com.name] = docstring

            else:
                docstring = command.help if command.help else "No docstring"
                help_items[command.name] = docstring
        return help_items

    async def build_message(self):
        items = await self.generate_help()
        message = await Macro.send(None)
        message.title = f"Page {self.index + 1} of {self.total} | {self.cogs[self.index]} cog"
        for item in items:
            message.add_field(name = f"{item}",
                              value = items[item],
                              inline = False)
        return message

        #for item in list()

    async def start(self):
        try:
            await self.paginator.start()
        except CancelledError:
            return

    async def prev(self):
        self.index = (self.index - 1 + self.total) % self.total
        await self.edit_message()

    async def next(self):
        self.index = (self.index + 1 + self.total) % self.total
        await self.edit_message()

    async def stop(self):
        await self.ctx.message.delete()
        await self.message.delete()
        await self.paginator.close()

    async def edit_message(self):
        await self.message.edit(embed = await self.build_message())


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def help_no_perms(self, message):
        """
        Ask Nolka for help without pagination
        """
        return await message.edit(embed = await Macro.Embed.error(
            "I can't start pagination without the `manage_messages` permission"
        ))

    @commands.command(pass_context = True)
    async def help(self, ctx):
        """
        Ask Nolka for help
        `-help`
        """
        message = await ctx.send(embed = await Macro.send("Getting help"))

        if not ctx.guild.me.permissions_in(ctx.channel).manage_messages:
            return await self.help_no_perms(message)

        helper = Helper(ctx, message)
        await helper.start()

    @commands.command(pass_context = True)
    async def invite(self, ctx, *args):
        """
        Return an OAuth link to add this bot to a server
        `-invite`
        """
        await ctx.channel.send(
            embed = await Macro.send("Add me to your server [here]({})".format(
                oauth_url(self.bot.user.id,
                          permissions = Permissions(permissions = 268443702))))
        )

    @commands.command(pass_context = True)
    async def report(self, ctx, *, report = None):
        """
        Report something to the bot owner `Zero#5200` so it appears in my channel
        `-report <something that happened with the bot ~~or your day~~>`
        """
        if not report:
            raise CustomPermissionError
        try:
            await ctx.bot.log.send(embed = await Macro.Embed.infraction(
                f"{ctx.author.name} from {ctx.guild} said this:\n{report}"))
        except Exception as error:
            await ctx.send(embed = await Macro.send("The report was not sent"))
            raise error
        await ctx.send(embed = await Macro.send("The report has been sent"))

    @commands.command(pass_context = True, aliases = ["rand"])
    async def random(self, ctx, *args):
        """
        Get a random number. Default is 0 to 10. One argument: 0 to argument. Two arguments: argument 1 to argument 2
        `-random [number] [number]`
        """
        try:
            args = tuple(map(int, args))
        except ValueError:
            args = ()
        if len(args) is 0:
            return await ctx.send(embed = await Macro.send(
                f"Random from 0 to 10: {randrange(0, 10)}"))

        if len(args) is 1:
            return await ctx.send(embed = await Macro.send(
                f"Random from 0 to {args[0]}: {randrange(0, args[0])}"))

        return await ctx.send(embed = await Macro.send(
            f"Random from {args[0]} to {args[1]}: {randrange(args[0], args[1])}"
        ))

    @commands.command(pass_context = True, aliases = ["colour"])
    async def color(self, ctx):
        """
        Get a random color
        `-color`
        """
        generated = randrange(0, 16777215)
        await ctx.send(
            embed = await Macro.send(hex(generated).replace("0x", "#").upper(),
                                     color = Color(generated)))

    @commands.group(pass_context = True, name = "prefix")
    async def prefix(self, ctx):
        """
        Get the prefixes used for Nolka on this guild
        `-prefix`
        """
        if ctx.invoked_subcommand is None:
            return await ctx.send(embed = await Macro.send(
                f"The guilds prefixes are {', '.join(await ctx.bot.command_prefix(ctx.bot, ctx.message))}"
            ))

    @commands.has_permissions(administrator = True)
    @prefix.command(pass_context = True, name = "set")
    async def prefix_set(self, ctx, *args):
        """
        Set Nolka's prefix for this guild
        `-prefix set <prefix>`
        """
        if not args:
            raise CustomPermissionError

        fix = args[0]

        if fix in await ctx.bot.command_prefix(ctx.bot, ctx.message):
            return await ctx.send(
                embed = await Macro.send(f"{fix} is already a prefix"))

        await ctx.bot.set_prefix(ctx, fix)

        return await ctx.send(embed = await Macro.send(f"{fix} was set"))

    @commands.has_permissions(administrator = True)
    @prefix.command(pass_context = True, name = "add")
    async def prefix_add(self, ctx, *args):
        """
        Add a prefix to Nolka's prefixes for this guild
        `-prefix add <prefixes>`
        """
        if not args:
            raise CustomPermissionError

        await ctx.bot.add_prefix(ctx, *args)

        return await ctx.send(embed = await Macro.send(
            f"{', '.join(args)} can now be used as a prefix"))

    @commands.has_permissions(administrator = True)
    @prefix.command(pass_context = True, name = "reset")
    async def prefix_reset(self, ctx):
        """
        Reset the prefix that Nolka uses on this guild
        `-prefix reset`
        """
        await ctx.bot.clear_prefix(ctx)

        return await ctx.send(
            embed = await Macro.send("The guild prefix was reset"))


def setup(bot):
    bot.add_cog(Utils(bot))
