import json
import random

import discord
import yaml
from discord import Intents
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands import has_permissions
import requests

reactions = {}
config = {}
invites = {}

intents = Intents.all()
client = commands.Bot(command_prefix="&", intents=intents)


def flush_data():
    with open('roles.yaml', 'w') as file:
        yaml.dump(reactions, file)
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file)


async def setup_data():
    with open('roles.yaml', 'r', encoding='utf8') as file:
        global reactions
        reactions = yaml.safe_load(file)
    with open('config.yaml', 'r', encoding='utf8') as file:
        global config
        config = yaml.safe_load(file)
    global invites
    for guild in client.guilds:
        invites[guild.id] = await guild.invites()


@client.event
async def on_ready():
    await setup_data()
    print('Der Bot wurde gestartet. Wird auch höchste Zeit digga!')


@client.command(
    name="purge",
    aliases=["pu"],
    help="Löscht Nachrichten im Kanal. Usage: &purge [amount] #Ohne Parameter werden alle Nachrichten gelöscht"
)
@has_permissions(manage_channels=True)
async def purge(ctx: Context, limit: int = 0):
    if limit == 0:
        await ctx.channel.purge()
    else:
        await ctx.channel.purge(limit=limit + 1)


@client.command(
    name="karottenlänge",
    aliases=["fler"],
    help="Zeigt die Länge von Flers Karotte"
)
async def send_carrot(ctx: Context):
    length = random.randint(1, 10)
    carrot = "<"
    for i in range(length):
        carrot += "="
    carrot += "3"
    embed = discord.Embed(title="**Deine Karotte:**", description=f"{ctx.author.name}s Karotte:\n{carrot}",
                          color=0x249bd6)
    await ctx.send(embed=embed)


@client.command(
    name="setup_roles"
)
@has_permissions(manage_channels=True)
async def setup_roles(ctx: Context):
    await ctx.message.delete()

    config['reaction_channel'] = ctx.channel.id
    flush_data()

    for column in range(len(reactions['roles'])):
        description = ""
        for element in range(1, len(reactions['roles'][column])):
            description += f"{reactions['roles'][column][element]}\n"
        embed = discord.Embed(title=reactions['roles'][column][0],
                              description=description,
                              color=0x249bd6)
        message = await ctx.send(embed=embed)
        for element2 in range(len(reactions['emojis'][column])):
            await message.add_reaction(reactions['emojis'][column][element2])


async def manage_role(payload, add):
    print(payload)
    if payload.channel_id == config['reaction_channel']:
        guild = await client.fetch_guild(payload.guild_id)
        for column in range(len(reactions['emojis'])):
            for element in range(len(reactions['emojis'][column])):
                if payload.emoji.name in reactions['emojis'][column][element]:
                    s = reactions['roles'][column][element + 1]
                    print(s)
                    s = s.split("・")[1]
                    start = s.find("<@&") + len("<@&")
                    end = s.find(">")
                    print(s[start:end])
                    role = discord.utils.get(guild.roles, id=int(s[start:end]))
                    if add:
                        await payload.member.add_roles(role)
                    else:
                        member = await guild.fetch_member(payload.user_id)
                        await member.remove_roles(role)


@client.event
async def on_raw_reaction_remove(payload):
    if payload.member is not client:
        await manage_role(payload, False)


@client.event
async def on_raw_reaction_add(payload):
    if payload.member is not client:
        await manage_role(payload, True)


def find_invite_by_code(invite_list, code):
    for inv in invite_list:
        if inv.code == code:
            return inv


def get_gif():
    apikey = "JOR8D5LX99HZ"
    lmt = 40
    search_term = "drinkbeer"
    r = requests.get(
        "https://g.tenor.com/v1/search?q=%s&key=%s&limit=%s" % (search_term, apikey, lmt))
    if r.status_code == 200:
        gif = json.loads(r.content)['results'][random.randint(0, lmt)]['media'][0]['gif']['url']
    else:
        gif = None
    return gif


@client.event
async def on_member_join(member):
    invites_before_join = invites[member.guild.id]
    invites_after_join = await member.guild.invites()
    for invite in invites_before_join:
        if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
            if invite.code == config['qr_invite_code']:
                role = discord.utils.get(member.guild.roles, id=config['qr_role_id'])
                await member.add_roles(role)
                invites[member.guild.id] = invites_after_join
                break
    embed = discord.Embed(title="Herzlich Willkommen",
                          description=f"Willkommen {member.mention}! :beers: :smoking: :beer: \nSchön dass du zu uns "
                                      "gefunden hast. "
                                      f"Lies bitte die <#{config['rules_channel']}> und hol dir die "
                                      f"<#{config['reaction_channel']}> ab, dann kannst du direkt " 
                                      "loslegen.   \n**Prost!**",
                          color=0x249bd6)
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_image(url=get_gif())
    channel = discord.utils.get(member.guild.text_channels, name="🔌•𝔴𝔦𝔩𝔩𝔨𝔬𝔪𝔪𝔢𝔫")
    await channel.send(embed=embed)


client.run('SECRET_KEY')
