import discord
from discord.ext import commands
import mysql.connector
import json

TOKEN = 'TOKEN_HERE'

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='yourdb'
)

with open('config.json', 'r') as file:
    config = json.load(file)


cursor = conn.cursor()

allowed_role_ids = config['allowed_role_ids']
intents = discord.Intents.all()
intents.typing = False

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Bot ist eingeloggt als {bot.user.name}')


@bot.command()
@commands.has_any_role('role1xx', 'xxxx')
async def findid(ctx, firstname: str, lastname: str):
   
    select_query = "SELECT id FROM users2 WHERE firstname = %s AND lastname = %s"
    params = (firstname, lastname)
    
    cursor.execute(select_query, params)
    result = cursor.fetchone()
    
    if result is None:
        embed = discord.Embed(title="Benutzer nicht gefunden", description=f"Der Benutzer '{firstname} {lastname}' wurde nicht in der Datenbank gefunden.", color=discord.Color.red())
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)
    else:
        user_id = result[0]
        embed = discord.Embed(title="Benutzer gefunden", description=f"Der Benutzer '{firstname} {lastname}' hat die ID '{user_id}'.", color=discord.Color.green())
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)


@findid.error
async def findid_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="Fehler", description="Du hast nicht alle erforderlichen Argumente angegeben.", color=discord.Color.red())
        embed.add_field(name="Verwendung", value="!findid <firstname> <lastname>", inline=False)
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CheckFailure):
        embed = discord.Embed(title="Fehler", description="Du besitzt keine Rolle mit Berechtigung zur Benutzersuche.", color=discord.Color.red())
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)


@bot.command()
@commands.has_any_role('role1xx', 'bbb')
async def syncuser(ctx, db_id: int, *, role_mention: discord.Role):
    user = ctx.author
    
    role = role_mention
    
    if not role:
        embed = discord.Embed(title="Fehler", description="Die angegebene Rolle existiert nicht.", color=discord.Color.red())
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)
        return
   
    update_query = "UPDATE users2 SET `group` = %s WHERE id = %s"
    params = (role.name, db_id)
    
    cursor.execute(update_query, params)
    conn.commit()

    embed = discord.Embed(title="Sync abgeschlossen", description=f"Die Synchronisierung für Datenbank ID {db_id} wurde erfolgreich durchgeführt. Die Benutzergruppe wurde in der Datenbank aktualisiert. Rolle: {role.mention}", color=discord.Color.green())
    embed.set_footer(text="Bot Sync")

    await ctx.send(embed=embed)


@syncuser.error
async def syncuser_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="Fehler", description="Du hast nicht alle erforderlichen Argumente angegeben.", color=discord.Color.red())
        embed.add_field(name="Verwendung", value="!syncuser <db_id> <@role>", inline=False)
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CheckFailure):
        embed = discord.Embed(title="Fehler", description="Du besitzt keine Rolle mit Berechtigung zur Benutzersynchronisierung.", color=discord.Color.red())
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)





@bot.command()
async def sync(ctx, db_id: int):
    user = ctx.author
    
    allowed_roles = [role for role in user.roles if role.id in allowed_role_ids]
    
    if len(allowed_roles) == 0:
        embed = discord.Embed(title="Fehler", description="Du besitzt keine Rolle mit Berechtigung zur Datenbankaktualisierung.", color=discord.Color.red())
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)
        return
    
    if len(allowed_roles) == 1:
        group_name = allowed_roles[0].name
    else:
        group_names = [role.name for role in allowed_roles]
        options = "\n".join([f"{index + 1}. {group_name}" for index, group_name in enumerate(group_names)])
        
        embed = discord.Embed(title="Gruppen-Auswahl", description=f"Du besitzt mehrere Rollen mit Berechtigung zur Datenbankaktualisierung. Bitte wähle eine Gruppe aus, indem du ihre Nummer eingibst.\n\n{options}", color=discord.Color.blue())
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()
        
        try:
            message = await bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Timeout", description="Du hast keine Auswahl getroffen.", color=discord.Color.red())
            embed.set_footer(text="Bot Sync")
            await ctx.send(embed=embed)
            return
        
        index = int(message.content) - 1
        if index < 0 or index >= len(allowed_roles):
            embed = discord.Embed(title="Ungültige Auswahl", description="Du hast eine ungültige Auswahl getroffen.", color=discord.Color.red())
            embed.set_footer(text="Bot Sync")
            await ctx.send(embed=embed)
            return
        
        group_name = allowed_roles[index].name
 
    update_query = "UPDATE users2 SET `group` = %s WHERE id = %s"
    params = (group_name, db_id)
    
    cursor.execute(update_query, params)
    conn.commit()
   
    embed = discord.Embed(title="Sync abgeschlossen", description=f"Die Synchronisierung für Datenbank ID {db_id} wurde erfolgreich durchgeführt. Die Benutzergruppe wurde in der Datenbank aktualisiert. Gruppe: {group_name}", color=discord.Color.green())
    embed.set_footer(text="Bot Sync")
 
    await ctx.send(embed=embed)




@bot.command()
async def users(ctx):
    select_query = "SELECT id, firstname, lastname FROM users2"
    
    cursor.execute(select_query)
    results = cursor.fetchall()
    
    if len(results) == 0:
        embed = discord.Embed(title="Keine Benutzer gefunden", description="Es wurden keine Benutzer in der Datenbank gefunden.", color=discord.Color.red())
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Benutzerliste", description="Liste aller Benutzer in der Datenbank:", color=discord.Color.blue())
        embed.set_footer(text="Bot Sync")
        
        for result in results:
            user_id = result[0]
            first_name = result[1]
            last_name = result[2]
            embed.add_field(name=f"ID: {user_id}", value=f"Name: {first_name} {last_name}", inline=False)
        
        await ctx.send(embed=embed)




@sync.error
async def sync_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="Fehler", description="Du hast nicht alle erforderlichen Argumente angegeben.", color=discord.Color.red())
        embed.add_field(name="Verwendung", value="!sync <db_id>", inline=False)
        embed.set_footer(text="Bot Sync")
        await ctx.send(embed=embed)

bot.run(TOKEN)
