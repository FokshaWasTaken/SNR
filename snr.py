import discord
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
import re
import math


class SNR(discord.Client):
	def __init__(self, mode, *args, **kwargs):
		self.mode = mode
		self.session = None
		self.time = get_current_time()
		super().__init__(*args, **kwargs)

	async def on_connect(self):
		self.session = aiohttp.ClientSession()

		if self.mode == 1:
			guilds = await self.fetch_guilds().flatten()
			servers = await self.fetch_servers(guilds)
			print_server_ranking(servers)
			await self.close()
		elif self.mode == 2:
			guild = self.get_guild(int(input("Input the guild ID you want to scan: ")))
			server = await self.fetch_server(guild)
			print(server)
			await self.close()
		elif self.mode == 3:
			print("React to any message in the server you want to scan!")

	async def on_raw_reaction_add(self, payload):
		if self.mode == 3:
			member = payload.member
			guild_id = payload.guild_id
			if member and guild_id:
				if member.id == self.user.id:
					await asyncio.sleep(1)
					guild = self.get_guild(guild_id)
					print(await self.fetch_server(guild))

	async def close(self):
		await super().close()
		await self.session.close()
		return

	async def fetch_servers(self, guilds):
		servers = []
		guild_amount = len(guilds)

		for i in range(0, guild_amount):
			print("-> Fetching guild {} out of {}.".format(i + 1, guild_amount), end="\r")
			guild = self.get_guild(guilds[i].id)
			server = await self.fetch_server(guild)
			servers.append(server)
			await asyncio.sleep(0.33)

		return servers

	async def fetch_server(self, guild):
		server = Server(guild)
		await server.fetch_drops(self.session, self.http.token, self.time)
		server.get_score()
		return server


class Server:
	def __init__(self, guild):
		self.member_count = guild.member_count
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

		pattern = r"(discord.com/gifts/|discordapp.com/gifts/|discord.gift/)[ ]*([a-zA-Z0-9]{16,24})([ ,.]|$)"
		seen_codes = []
		for message_list in json_response["messages"]:
			message = next(m for m in message_list if m.get("hit"))
			content = message["content"]
			match = re.search(pattern, content)
			if match and match.group(2) not in seen_codes:
				code = match.group(2)
				self.nitro_drops.append(Drop(code, message["timestamp"], current_time))
				seen_codes.append(code)
			else:
				self.fake_count += 1

	def get_score(self):
		if self.score != -1:
			return self.score

		server_count = self.member_count
		server_count_effect = (-(1 / (server_count / 15000 + 0.5) - 1.2) ** 2) / 1.44 + 1

		nitro_effect = sum(drop.get_score() for drop in self.nitro_drops)

		self.score = nitro_effect * server_count_effect
		return self.score

	def __repr__(self):
		return "({}) - {} (Fakes: {})".format(self.name, round(self.score, 2), self.fake_count)


class Drop:
	def __init__(self, code, timestamp, current_time):
		send_date = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z")
		self.seconds_since = timedelta.total_seconds(current_time - send_date)
		self.code = code

	def get_score(self):
		time_effect = 2**(-self.seconds_since/1209600)
		probability_effect = self.get_code_legitimacy_probability()
		return time_effect * probability_effect

	def get_code_legitimacy_probability(self):
		lower = upper = numeric = 0

		for c in self.code:
			if c.isnumeric():
				numeric += 1
			elif c.isupper():
				upper += 1
			else:
				lower += 1

		length = len(self.code)
		percentage_lower = lower / length
		percentage_upper = upper / length
		percentage_numeric = numeric / length

		chance_char = 26 / 62
		chance_num = 10 / 62

		error_lower = abs(chance_char - percentage_lower)
		error_upper = abs(chance_char - percentage_upper)
		error_numeric = abs(chance_num - percentage_numeric)

		error_amount = error_lower + error_upper + error_numeric
		error = 1 / (1 + math.exp(error_amount * 25 - 15))
		return error


def get_current_time():
	current_time = datetime.now()
	return current_time.replace(tzinfo=timezone.utc)


def print_server_ranking(servers):
	ranked = sorted(servers, key=Server.get_score, reverse=True)
	for i in range(0, len(ranked)):
		print("{} -> {}".format(i+1, ranked[i]))


if __name__ == "__main__":
	print("Welcome to SNR.")
	user_token = input("Please input the token you want to scan: ")
	function_mode = int(input("Pick mode (1 - Scan All, 2 - Scan One, 3 - Live Scan): "))
	client = SNR(function_mode)
	client.run(user_token, bot=False)
