import xml.etree.ElementTree as ET
import requests, discord, json, os
from logging import getLogger, INFO, StreamHandler, Formatter
from discord.ext import tasks

logger = getLogger(__name__)
logger.setLevel(INFO)
logger_handler = StreamHandler()
logger_formatter = Formatter(fmt='%(asctime)-15s [%(name)s] %(message)s')
logger_handler.setFormatter(logger_formatter)
logger.addHandler(logger_handler)

client = discord.Client()
code_folder = os.path.join(os.getcwd(), os.path.dirname(__file__))
config = json.load(open(os.path.join(code_folder, 'config/config.json')))
TOKEN = config['DISCORD_TOKEN']
SITES = config['sites']
CHANNEL_ID = config['CHANNEL_ID']
ADS = []
if "Ads" in config:
    for ad in config['Ads']:
        ADS.append(ad)

CHECKED_IDS = []
if os.path.exists(os.path.join(code_folder, 'checked_ids.txt')):
    with open(os.path.join(code_folder, 'checked_ids.txt'), 'r') as f:
        CHECKED_IDS = f.read().splitlines()

@client.event
async def on_ready():
    logger.info("Logged in as {}".format(client.user.name))

def parse_rss(url):
    domain = url.split('/')[2]
    response = requests.get(url)
    root = ET.fromstring(response.content)
    title = root.find('channel/title').text
    items = root.findall('.//item')
    favicon = "https://www.google.com/s2/favicons?domain=%s" % (domain)
    articles = []
    for item in items:
        title = item.find('.//title').text
        link = item.find('.//link').text
        description = item.find('.//description').text
        if item.find('.//guid') is not None:
            guid = item.find('.//guid').text
        else:
            guid = link
        if item.find('.//enclosure') is not None:
            image = item.find('.//enclosure').get('url')
        else:
            image = None
        articles.append({
            'title': title,
            'link': link,
            'description': description,
            'guid': guid,
            'image': image
        })
    return title, domain, favicon, articles

@tasks.loop(seconds=10)
async def loop():
    global CHECKED_IDS
    for url in SITES:
        title, favicon, domain, articles = parse_rss(url)
        for article in articles:
            if article['guid'] not in CHECKED_IDS:
                CHECKED_IDS.append(article['guid'])
                with open(os.path.join(code_folder, 'checked_ids.txt'), 'a') as f:
                    f.write(article['guid'] + '\n')
                embed = discord.Embed(title=article['title'], url=article['link'], description=article['description'])
                if article['image'] is not None:
                    embed.set_image(url=article['image'])
                embed.set_author(name=title, icon_url=favicon, url="https://%s" % (domain))
                for ad in ADS:
                    embed.add_field(name=ad['title'], value=ad['description'])
                await client.get_channel(CHANNEL_ID).send(embed=embed)

if __name__ == "__main__":
    client.start(TOKEN)