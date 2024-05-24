from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from requests import get
import csv
import json 
import time
import base64
from pytoniq_core import Address
from dotenv import dotenv_values

config = dotenv_values(".env")
apiKey = config["API_KEY_TONCENTER"]
teleKey = config["API_KEY_TELE"]
queryURL = "https://toncenter.com/api/v3"
collectionAddress = ""
itemIndex = 0
apiKeyHeaders = {
    "X-API-Key": apiKey
}

def fechCollectionInfo(owner_address):

    res = get(
        f"{queryURL}/nft/collections?owner_address={owner_address}&limit=256&offset=0",
        headers=apiKeyHeaders
    )
    dataRaw = res.json()
    infoCollection = dataRaw['nft_collections']
    for data in infoCollection:
        if data["next_item_index"] == -1:
            print("Can't track this collection right now")
        else:
            return infoCollection

def fechHolderNft(collection_address,indexLimit):
    index = 0
    map = {}
    with open("holder.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Index", "Holder Address"])
        while True:
            if index >= int(indexLimit):
                break
            res = get(
                f"{queryURL}/nft/items?collection_address={collection_address}&limit=256&offset={index}&api_key={apiKey}",
            )
            dataRaw = res.json()    
            

            listHolder = dataRaw["nft_items"]
            for dataHolder in listHolder:
                hexAddress = dataHolder["owner_address"]
                address = Address(hexAddress)
                writer.writerow([dataHolder["index"], address.to_str()])

            index += 256
            time.sleep(1)
    print("Done!")

async def snapshotNFT(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = update.message.text.partition(" ")[2]
    collectionInfo = fechCollectionInfo(data)

    for data in collectionInfo:
        collectionAddress = data["address"]
        indexLimit = data["next_item_index"]

    fechHolderNft(collectionAddress,indexLimit)
    await context.bot.send_document(chat_id=update.message.chat_id,document=open('holder.csv', 'rb'), filename="holder.csv")
    
app = ApplicationBuilder().token(teleKey).build()

app.add_handler(CommandHandler("snapshot", snapshotNFT))

app.run_polling()