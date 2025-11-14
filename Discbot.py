from IPython import embed
import discord
from discord import Interaction, app_commands
import requests
import datetime
import os 
from dotenv import load_dotenv

STORE_MAP = {
    "Steam" : 1,
    "Epic" : 25,
    "GOG" : 6,
    "Todas" : [1, 6, 25],
}

CHEAPSHARK_API_URL = "https://www.cheapshark.com/api/1.0/deals"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def get_deals(store_name: str, limit: int = 10):
    params = {
        'sortBy': 'Recent',
        'pageSize': limit,
    }

    store_id = STORE_MAP.get(store_name.lower())
    if store_id is not None:
        params['storeID'] = store_id

    try:
        response = requests.get(CHEAPSHARK_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al conectar con la API de CheapShark: {e}")
        return None

def date_start_strftime(format):
    raise NotImplementedError
    
@tree.command(name="ofertas", description="Obtén los ultimos juegos con ofertas o gratis de Steam, Epic, GOG, o todas.")
@app_commands.describe(tienda="Filtra por tienda especifica.")
@app_commands.choices(tienda=[
    app_commands.Choice(name="Steam", value="Steam"),
    app_commands.Choice(name="Epic", value="Epic"),
    app_commands.Choice(name="GOG", value="GOG"),
    app_commands.Choice(name="Todas", value="Todas"),
])
async def deals_command(interaction: discord.Interaction, tienda: app_commands.Choice[str]):
    await interaction.response.defer()
    store_name = tienda.value
    deals = get_deals(store_name)
    if not deals:
        await interaction.followup.send(
            f"**Error:** No se pudo conectar a la API de ofertas o no se encontraron datos para **{store_name.upper()}**.", ephemeral= True
        )
    
    store_title = store_name.upper() if store_name !="Todas" else "TODAS LAS TIENDAS"
    embed = discord.Embed(
        title = f"Mejores ofertas recientes - {store_title}",
        description = f"Se encontraron **{len(deals)}** ofertas recientes.",
        color = discord.Color.blue()
    )

    for deal in deals:
        sale_price =float(deal['salePrice'])
        normal_price = float (deal['normalPrice'])
        savings_percent = float(deal['savings'])

        current_store = (
            "Steam" if deal['storeID'] == "1" else
            "GOG" if deal['storeID'] == "6" else
            "Epic" if deal['storeID'] == "25" else
            "Otra Tienda"
        )

        timestamp = int(deal['"LastChange'])
        date_star = datetime.datetime.fromtimestamp(timestamp)
        date_start_str = date_start_strftime("%d/%m/%Y")

        price_status = ""
        if sale_price == 0.0:
            price_status = "**¡Gratis!**"
        else:
            price_status = (f"~~${normal_price:.2f}~~ ➔ **${sale_price:.2f}**"
            f"(-{savings_percent:.0f}%)"
        )

        deal_id = deal['dealID']
        deal_url = f"https://www.cheapshark.com/redirect?dealID={deal_id}"

        field_value = (
            f"{price_status}\n",
            f"Tienda: **{current_store}**\n",
            f"Iniciado: **{date_start_str}**\n",
            f"[Ver Oferta]({deal_url})"
        )

        embed.add.field(name=deal['title'], value="".join(field_value), inline=False)

        embed.set.footer(text="Datos proporcionados por CheapShark.com | Solicitado por {interaction.user.name}", icon_url=Interaction.user.avatar.url)

    await Interaction.followup.send(embed=embed)

@client.event
async def on_ready():
    await tree.sync()
    print(f'Bot conectado como {client.user}')
    print('Listo para recibir comandos!')

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if TOKEN is None:
    print("Error: La variable de entorno DISCORD_BOT_TOKEN no está establecida.")
    print("Asegúrate de tener un archivo .env con el token correcto.")
else:
    client.run(TOKEN)
