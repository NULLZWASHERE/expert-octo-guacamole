from http.server import BaseHTTPRequestHandler
import json
import aiohttp
import asyncio
from urllib.parse import urlparse

# Approximate Roblox User ID ranges by year (updated as of 2026)
YEAR_RANGES = {
    2006: (1, 1000),
    2007: (1000, 50000),
    2008: (50000, 300000),
    2009: (300000, 1500000),
    2010: (1500000, 5000000),
    2011: (5000000, 15000000),
    2012: (15000000, 40000000),
    2013: (40000000, 80000000),
    2014: (80000000, 150000000),
    2015: (150000000, 300000000),
    2016: (300000000, 600000000),
    2017: (600000000, 1200000000),
    2018: (1200000000, 2500000000),
    2019: (2500000000, 4500000000),
    2020: (4500000000, 8000000000),
    2021: (8000000000, 14000000000),
    2022: (14000000000, 22000000000),
    2023: (22000000000, 32000000000),
    2024: (32000000000, 45000000000),
    2025: (45000000000, 60000000000),
    2026: (60000000000, 80000000000),
}

async def get_username_from_id(user_id: int, session: aiohttp.ClientSession):
    try:
        async with session.get(f"https://users.roblox.com/v1/users/{user_id}", timeout=8) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "id": user_id,
                    "username": data.get("name"),
                    "displayName": data.get("displayName"),
                    "created": data.get("created"),
                    "isBanned": data.get("isBanned", False)
                }
            elif resp.status == 404:
                return {"id": user_id, "status": "not_found"}
            else:
                return {"id": user_id, "status": "error", "code": resp.status}
    except:
        return {"id": user_id, "status": "timeout"}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            year = data.get("year")
            count = data.get("count", 100)          # default 100
            start_id = data.get("start_id")
            check = data.get("check", True)         # whether to resolve usernames
            max_concurrent = 30                     # safe concurrency

            if year:
                if year not in YEAR_RANGES:
                    self.send_error(400, "Year not supported")
                    return
                min_id, max_id = YEAR_RANGES[year]
                if start_id:
                    min_id = max(min_id, start_id)
            elif start_id:
                min_id = start_id
                max_id = start_id + count * 5
            else:
                min_id = 1
                max_id = 1000000

            # Generate IDs
            generated_ids = list(range(min_id, min(max_id, min_id + count * 10), max(1, (max_id - min_id) // count)))

            result = {
                "year": year,
                "ids_generated": len(generated_ids),
                "users": []
            }

            if check:
                async def fetch_all():
                    async with aiohttp.ClientSession() as session:
                        tasks = []
                        for uid in generated_ids[:count]:   # respect requested count
                            tasks.append(get_username_from_id(uid, session))
                            if len(tasks) >= max_concurrent:
                                result["users"].extend(await asyncio.gather(*tasks))
                                tasks = []
                        if tasks:
                            result["users"].extend(await asyncio.gather(*tasks))
                
                asyncio.run(fetch_all())
            else:
                result["users"] = [{"id": uid} for uid in generated_ids[:count]]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "endpoints": "/api/users",
            "usage": {
                "year": "2006-2026",
                "count": "number of IDs to generate/check (no hard limit)",
                "check": "true/false - resolve usernames",
                "start_id": "optional custom starting ID"
            },
            "example": {
                "year": 2012,
                "count": 500,
                "check": True
            }
        }).encode())
