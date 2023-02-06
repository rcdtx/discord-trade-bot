import collections
import os

import requests
import discord

from discord.ext import commands
from prettytable import PrettyTable

discord_bot_key = os.environ["DISCORD_BOT_KEY"]

# Initialize user's balances
balances = collections.defaultdict(lambda: collections.defaultdict(float))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=">", intents=intents)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id

    if message.content.startswith("!buy"):
        # Get current price of symbol from CoinGecko API
        symbol = message.content.split()[1]
        amount = float(message.content.split()[2])

        if user_id in balances:
            if balances[user_id]["usd"] >= amount:
                price = get_price(symbol)

                if price is None:
                    await message.channel.send(
                        f"{message.author.mention}, Unable to retrieve the price for {symbol}."
                    )
                    return

                balances[user_id]["usd"] -= amount
                purchase_amount = amount / price
                balances[user_id][symbol] += purchase_amount

                table = PrettyTable()

                table.field_names = ["symbol", "amount"]

                for key, value in balances[user_id].items():
                    table.add_row([key, value])

                await message.channel.send(
                    f"{message.author.mention}, you have successfully bought {purchase_amount} of {symbol} at ${price}. Your new balance is {table}"
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
        symbol = message.content.split()[1]
        amount = float(message.content.split()[2])

        # Get current price of symbol from CoinGecko API
        price = get_price(symbol)

        if user_id in balances:
            if amount > 0 and amount <= balances[user_id][symbol]:
                balances[user_id]["usd"] += price * amount
                balances[user_id][symbol] -= amount

            else:
                await message.channel.send(
                    f"{message.author.mention}, you do not have enough {symbol} in your account to sell {amount}."
                )
                return
            table = PrettyTable()

            table.field_names = ["symbol", "amount"]

            for key, value in balances[user_id].items():
                table.add_row([key, value])

            await message.channel.send(
                f"{message.author.mention}, you have successfully sold {amount} of {symbol} for ${price}. Your new balance is {table}"
            )
        else:
            await message.channel.send(
                f"{message.author.mention}, you do not have an account set up. Please use !balance to set up your account"
            )

    elif message.content.startswith("!balance"):
        if user_id in balances:
            await message.channel.send(
                f"{message.author.mention}, your balance is ${balances[user_id]}"
            )
        else:
            balances[user_id]["usd"] = 1000.0

            await message.channel.send(
                f"{message.author.mention}, an account has been set up for you with a balance of ${balances[user_id]}"
            )

    elif message.content.startswith("!leaderboard"):
        await message.channel.send(await sort_and_convert_leaderboard())


def get_price(symbol: str) -> float:
    coins_list = requests.get("https://api.coingecko.com/api/v3/coins/list").json()

    for coin in coins_list:
        if coin["symbol"] == symbol:
            coin_id = coin["id"]
            break
        else:
            coin_id = None

    if coin_id:
        price = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        ).json()[coin_id]["usd"]
    else:
        print(f"Error: Symbol '{symbol}' not found in CoinGecko API")
        price = None

    return float(price)


async def sort_and_convert_leaderboard() -> dict:
    # Sort the users by their balance
    sorted_leaderboard = dict(
        sorted(balances.items(), key=lambda item: item[1], reverse=True)
    )
    sorted_and_converted_leaderboard = {}
    for user_id, score in sorted_leaderboard.items():
        user = await bot.fetch_user(user_id)
        if user is not None:
            username = user.name
            sorted_and_converted_leaderboard[username] = score
    return sorted_and_converted_leaderboard


if __name__ == "__main__":
    try:
        bot.run(discord_bot_key)
    except discord.HTTPException as e:
        if e.status == 429:
            print("discord rate limit issue... restarting")
            os.system("kill 1")
        else:
            raise e
