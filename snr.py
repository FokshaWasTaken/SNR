import discord
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
import re


class SNR(discord.Client):
	def __init__(self, mode, *args, **kwargs):
		self.mode = mode
		self.session = None
		super().__init__(*args, **kwargs)

	async def on_connect(self):
		self.session = aiohttp.ClientSession()
		account_token = self.http.token
		current_time = get_current_time()

		if self.mode == 1:
			guilds = await self.fetch_guilds().flatten()
			servers = await fetch_servers(guilds, account_token, self.session, current_time)
			rank_servers(servers)
			await self.close()
		elif self.mode == 2:
			guild = self.get_guild(int(input("Input the guild ID you want to scan: ")))
			server = await fetch_server(guild, account_token, self.session, current_time)
			print(server)
			await self.close()
		elif self.mode == 3:
			print("Waiting for you to join a server...", end="\r")

	async def on_guild_join(self, guild):
		if self.mode == 3:
			server = await fetch_server(guild, self.http.token, self.session, get_current_time())
			print(server)

	async def close(self):
		await super().close()
		await self.session.close()


class Server:
	def __init__(self, guild):
		self.member_count = len(guild.members)
		self.name = guild.name
		self.id = guild.id
		self.nitro_drops = []
		self.score = -1
		self.fake_count = 0

	async def fetch_drops(self, session, account_token, current_time):
		json_response = {}
		while json_response.get("messages") is None:
			search_query = "discord.gift"
			base_api_url = "https://discordapp.com/api/v8/guilds/{}/messages/search?content={}&include_nsfw=true"
			url = base_api_url.format(self.id, search_query)
			headers = {"authorization": account_token}

			response = await session.get(url, headers=headers)
			json_response = await response.json()

			if json_response.get("message") == "You are being rate limited.":
				rate_limit = json_response["retry_after"]
				print("-> Being rate-limited. Please wait {}...".format(rate_limit), end="\r")
				await asyncio.sleep(rate_limit)

			if json_response.get("message") == "Index not yet available. Try again later":
				print("-> Guild {} is unindexed. Skipping.".format(self.name), end="\r")
				return

		pattern = r"(discord.com/gifts/|discordapp.com/gifts/|discord.gift/)[ ]*([a-zA-Z0-9]{16,24})"
		seen_codes = []
		for message_list in json_response["messages"]:
			message = next(m for m in message_list if m.get("hit"))
			content = message["content"]
			match = re.search(pattern, content)
			if match and match.group(2) not in seen_codes:
				send_date = datetime.strptime(message["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z")
				seconds_since = timedelta.total_seconds(current_time - send_date)
				self.nitro_drops.append(seconds_since)
				seen_codes.append(match.group(2))
			else:
				self.fake_count += 1

	def get_score(self):
		if self.score != -1:
			return self.score

		server_count = self.member_count
		server_count_effect = (-(1 / (server_count / 15000 + 0.5) - 1.2) ** 2) / 1.44 + 1

		drops = self.nitro_drops
		nitro_effect = 0
		for drop in drops:
			nitro_effect += 2**(-drop/1209600)

		self.score = nitro_effect * server_count_effect
		return self.score

	def __repr__(self):
		return "({}) - {} (Fakes: {})".format(self.name, round(self.score, 2), self.fake_count)


def get_current_time():
	current_time = datetime.now()
	return current_time.replace(tzinfo=timezone.utc)


async def fetch_servers(guilds, account_token, session, current_time):
	servers = []
	guild_amount = len(guilds)

	for i in range(0, guild_amount):
		print("-> Fetching guild {} out of {}.".format(i+1, guild_amount), end="\r")
		server = await fetch_server(guilds[i], account_token, session, current_time)
		servers.append(server)
		await asyncio.sleep(0.33)

	return servers


async def fetch_server(guild, account_token, session, current_time):
	server = Server(guild)
	await server.fetch_drops(session, account_token, current_time)
	server.get_score()
	return server


def rank_servers(servers):
	ranked = sorted(servers, key=Server.get_score, reverse=True)
	for i in range(0, len(ranked)):
		print("{} -> {}".format(i+1, ranked[i]))


if __name__ == "__main__":
	print("Welcome to SNR.")
	user_token = input("Please input the token you want to scan: ")
	function_mode = int(input("Pick mode (1 - Scan All, 2 - Scan One, 3 - Live Scan): "))
	client = SNR(function_mode)
	client.run(user_token, bot=False)
