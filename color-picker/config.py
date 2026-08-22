import os
import json


def load_env_file():
	"""Read the .env sitting next to this file into the environment.

	Nothing else loads it, so a variable added to .env would otherwise never
	reach the process unless it happened to already be exported in the shell
	that started the bot. Existing environment variables always win, so
	deployed secrets are never overridden by a stale file.
	"""
	env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
	if not os.path.exists(env_path):
		return

	with open(env_path) as file:
		for line in file:
			line = line.strip()
			if not line or line.startswith("#") or "=" not in line:
				continue

			key, _, value = line.partition("=")
			key = key.strip()
			value = value.strip()

			if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
				value = value[1:-1]

			os.environ.setdefault(key, value)


load_env_file()

configuration = {}

try:
  if os.environ["ENVIRONMENT"] == "PRODUCTION":
    configuration = {
			"guild_id": int(os.environ["GUILD_ID"]),
			"connection_string": os.environ["CONNECTION_STRING"],
			"token": os.environ["TOKEN"],
			# Optional: without it, actions just aren't logged anywhere.
			"botspam_channel_id": int(os.environ["BOTSPAM_CHANNEL_ID"])
				if os.environ.get("BOTSPAM_CHANNEL_ID") else None,
    }
except KeyError:
	with open("config.json", "r") as file:
		configuration = json.load(file)

import psycopg2_pool

pool = psycopg2_pool.ConnectionPool(minconn=5, maxconn=20, dsn=configuration["connection_string"], idle_timeout=60)

def select_one(query, params):
	with pool.getconn() as conn:
		with conn.cursor() as cursor:
			cursor.execute(query, params)
			result = cursor.fetchone()
	
	return result

def execute_query(query, params):
	with pool.getconn() as conn:
		with conn.cursor() as cursor:
			cursor.execute(query, params)
		conn.commit()

# Mirrors util.set_maaldar_role_info. The bot's util imports dependencies this
# process doesn't have, so the snapshot write is duplicated rather than shared.
DAYS_IN_SECONDS_REQUIRED_FOR_ROLE = 15_552_000

def set_maaldar_role_info(user_id, role_name, role_color):
	duration = select_one(
		"SELECT boosting_since FROM MaaldarDuration WHERE user_id = %s", (str(user_id),)
	)
	if duration is None or duration[0] < DAYS_IN_SECONDS_REQUIRED_FOR_ROLE:
		return

	existing = select_one(
		"SELECT user_id FROM MaaldarRoles WHERE user_id = %s", (str(user_id),)
	)
	if existing is None:
		execute_query(
			"INSERT INTO MaaldarRoles VALUES (%s, %s, %s)",
			(str(user_id), role_name, role_color)
		)
	else:
		execute_query(
			"UPDATE MaaldarRoles SET role_name = %s, role_color = %s WHERE user_id = %s",
			(role_name, role_color, str(user_id))
		)

from colorthief import ColorThief
import aiohttp
from io import BytesIO

async def get_buffer_from_url(url):
	buffer: BytesIO
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as response:
			if response.status == 200:
				buffer = BytesIO(await response.read())
	
	return buffer

async def get_dominant_colors(member_avatar_url):
	buffer = await get_buffer_from_url(member_avatar_url)
	color_palette = ColorThief(buffer).get_palette()

	dominant_colors = [rgb_to_hex(color) for color in color_palette]
	
	return dominant_colors

def rgb_to_hex(rgb):
	return "%02x%02x%02x" % (rgb)


# --- Role icons -------------------------------------------------------------

import asyncio
import base64
import ipaddress
import socket
from urllib.parse import urlparse

# Discord caps role icons at 256 KB and only accepts PNG/JPEG.
MAX_ICON_BYTES = 256 * 1024
# An image only being used as a source to crop from gets a looser ceiling,
# since the crop re-encodes it well under MAX_ICON_BYTES.
MAX_SOURCE_BYTES = 10 * 1024 * 1024


def sniff_image_type(data):
	"""Return the image format from the file's magic bytes, or None.

	Content-Type headers and file extensions are attacker-controlled, so the
	actual bytes are what we trust. Covers more than Discord accepts, because
	anything the browser can decode is a valid source to crop from.
	"""
	if data.startswith(b"\x89PNG\r\n\x1a\n"):
		return "png"
	if data.startswith(b"\xff\xd8\xff"):
		return "jpeg"
	if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
		return "gif"
	if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
		return "webp"
	return None


def _is_public_ip(address):
	try:
		ip = ipaddress.ip_address(address)
	except ValueError:
		return False

	return not (
		ip.is_private
		or ip.is_loopback
		or ip.is_link_local
		or ip.is_multicast
		or ip.is_reserved
		or ip.is_unspecified
	)


def decode_image_data_uri(value):
	"""Decode a "data:image/png;base64,..." string into raw bytes."""
	if not value.startswith("data:"):
		raise ValueError("Expected an image file")

	header, separator, encoded = value.partition(",")
	if not separator or "base64" not in header:
		raise ValueError("Expected a base64-encoded image")

	# Check the encoded length first so an oversized blob is rejected before
	# it's expanded into memory. base64 inflates by ~4/3, so this is generous.
	if len(encoded) > MAX_ICON_BYTES * 2:
		raise ValueError("Image is larger than 256 KB")

	try:
		data = base64.b64decode(encoded, validate=True)
	except Exception:
		raise ValueError("That image couldn't be read")

	if len(data) > MAX_ICON_BYTES:
		raise ValueError("Image is larger than 256 KB")

	return data


async def fetch_image_from_url(url, max_bytes=MAX_ICON_BYTES):
	"""Fetch a user-supplied image URL, with SSRF guards and a hard size cap.

	Raises ValueError with a user-facing message on any rejection. Unlike
	get_buffer_from_url (which only ever sees trusted Discord CDN links), this
	takes arbitrary user input, so it refuses anything resolving into private
	address space and refuses to follow redirects.
	"""
	parsed = urlparse(url)

	if parsed.scheme not in ("http", "https"):
		raise ValueError("Only http and https links are supported")
	if not parsed.hostname:
		raise ValueError("That doesn't look like a valid link")

	port = parsed.port or (443 if parsed.scheme == "https" else 80)

	try:
		resolved = await asyncio.get_running_loop().getaddrinfo(
			parsed.hostname, port, proto=socket.IPPROTO_TCP
		)
	except socket.gaierror:
		raise ValueError("Couldn't resolve that link")

	# Every address the host resolves to must be public, so a link can't be
	# used to reach the database, cloud metadata endpoints or anything else
	# on the internal network.
	for *_, sockaddr in resolved:
		if not _is_public_ip(sockaddr[0]):
			raise ValueError("That link points to a private address")

	timeout = aiohttp.ClientTimeout(total=10)
	async with aiohttp.ClientSession(timeout=timeout) as session:
		# allow_redirects=False: a redirect could otherwise bounce us to an
		# internal address after the check above has already passed.
		async with session.get(url, allow_redirects=False) as response:
			if response.status in (301, 302, 303, 307, 308):
				raise ValueError("That link redirects, so paste the direct image link")
			if response.status != 200:
				raise ValueError(f"The link returned HTTP {response.status}")

			chunks = []
			total = 0
			async for chunk in response.content.iter_chunked(8192):
				total += len(chunk)
				if total > max_bytes:
					raise ValueError(f"Image is larger than {max_bytes // 1024} KB")
				chunks.append(chunk)

	return b"".join(chunks)
