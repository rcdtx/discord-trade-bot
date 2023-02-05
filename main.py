import os

import requests
import discord
from discord.ext import commands

discord_bot_key = os.environ["DISCORD_BOT_KEY"]

# Initialize user's balances
balances = {}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=">", intents=intents)


@bot.event
async def on_message(message):
    if message.content.startswith("!buy"):
        ticker = message.content.split()[1]
        # Get current price of ticker from CoinGecko API
        price = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ticker}&vs_currencies=usd"
        ).json()[ticker]["usd"]
        user_id = str(message.author.id)
        if user_id in balances:
            if balances[user_id] >= price:
                balances[user_id] -= price
                await message.channel.send(
                    f"{message.author.mention}, you have successfully bought {ticker} for ${price}. Your new balance is ${balances[user_id]}"
                )
            else:
                await message.channel.send(
                    f"{message.author.mention}, you do not have enough funds to make this purchase."
                )
        else:
            await message.channel.send(
                f"{message.author.mention}, you do not have an account set up. Please use !balance to set up your account"
            )

    elif message.content.startswith("!sell"):
        ticker = message.content.split()[1]
        # Get current price of ticker from CoinGecko API
        price = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ticker}&vs_currencies=usd"
        ).json()[ticker]["usd"]
        user_id = str(message.author.id)
        if user_id in balances:
            balances[user_id] += price
            await message.channel.send(
                f"{message.author.mention}, you have successfully sold {ticker} for ${price}. Your new balance is ${balances[user_id]}"
            )
        else:
            await message.channel.send(
                f"{message.author.mention}, you do not have an account set up. Please use !balance to set up your account"
            )

    elif message.content.startswith("!balance"):
        user_id = str(message.author.id)
        if user_id in balances:
            await message.channel.send(
                f"{message.author.mention}, your balance is ${balances[user_id]}"
            )
        else:
            balances[user_id] = 1000
            await message.channel.send(
                f"{message.author.mention}, an account has been set up for you with a balance of ${balances[user_id]}"
            )

    elif message.content.startswith("!leaderboard"):
        # Sort the users by their balance
        sorted_balances = sorted(balances.items(), key=lambda x: x[1], reverse=True)
        leaderboard_message = f"{sorted_balances}\n"
        await message.channel.send(leaderboard_message)


if __name__ == "__main__":
    try:
        bot.run(discord_bot_key)
    except discord.HTTPException as e:
        if e.status == 429:
            print("rate limit issue... restarting")
            os.system("kill 1")
        else:
            raise e
