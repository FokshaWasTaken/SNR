import discord
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
import re


class SNR(discord.Client):
	async def on_connect(self):
		servers = await fetch_servers(await self.fetch_guilds().flatten(), self.http.token)
		rank_servers(servers)
		await self.close()


class Server:
	def __init__(self, guild):
		self.member_count = len(guild.members)
		self.name = guild.name
		self.id = guild.id
		self.nitro_drops = []
		self.score = 0

	async def fetch_drops(self, session, account_token, current_time):
		search_query = "discord.gift"
		base_api_url = "https://discordapp.com/api/v8/guilds/{}/messages/search?content={}&include_nsfw=true"
		url = base_api_url.format(self.id, search_query)
		headers = {"authorization": account_token}

		response = await session.get(url, headers=headers)
		json_response = await response.json()

		pattern = r"(discord.com/gifts/|discordapp.com/gifts/|discord.gift/)[ ]*([a-zA-Z0-9]{16,24})"
		for message_list in json_response["messages"]:
			message = message_list[2]
			content = message["content"]
			if re.search(pattern, content):
				send_date = datetime.strptime(message["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z")
				seconds_since = timedelta.total_seconds(current_time - send_date)
				self.nitro_drops.append(seconds_since)

	def get_score(self):
		server_count = self.member_count
		server_count_effect = (-(1 / (server_count / 15000 + 0.5) - 1.2) ** 2) / 1.44 + 1

		drops = self.nitro_drops
		nitro_effect = 0
		for drop in drops:
			nitro_effect += 2**(-drop/1209600)

		self.score = nitro_effect * server_count_effect
		return self.score

	def __repr__(self):
		return "({}) - {}".format(self.name, self.score)


async def fetch_servers(guilds, account_token):
	current_time = datetime.now()
	current_time = current_time.replace(tzinfo=timezone.utc)

	session = aiohttp.ClientSession()
	servers = []

	guild_amount = len(guilds)

	for i in range(0, guild_amount):
		print("-> Fetching guild {} out of {}.".format(i+1, guild_amount), end="\r")
		server = Server(guilds[i])
		await server.fetch_drops(session, account_token, current_time)
		servers.append(server)
		await asyncio.sleep(0.33)

	await session.close()
	return servers


def rank_servers(servers):
	ranked = sorted(servers, key=Server.get_score, reverse=True)
	for i in range(0, len(ranked)):
		print("{} -> {}".format(i+1, ranked[i]))


if __name__ == "__main__":
	print("Welcome to SNR.")
	user_token = input("Please input the token you want to scan: ")
	client = SNR()
	client.run(user_token, bot=False)
