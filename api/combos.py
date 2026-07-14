from http.server import BaseHTTPRequestHandler
import json
import re

def generate_combos(username: str) -> list[str]:
    combos = set()
    u = username.strip()
    if not u:
        return []
    
    # 1. Username as password
    combos.add(f"{u}:{u}")
    combos.add(f"{u}:{u.lower()}")
    combos.add(f"{u}:{u.upper()}")
    
    # Extract numbers and letters
    numbers = re.findall(r'\d+', u)
    letters = re.sub(r'\d+', '', u).strip()
    full_num = ''.join(numbers)
    
    # Common number patterns
    common_nums = ['11', '12', '123', '69', '420', '00', '01', '777', '999', '000', '666', '321', '007']
    
    # Base variations
    if letters:
        for num in common_nums:
            combos.add(f"{u}:{letters}{num}")
            combos.add(f"{u}:{num}{letters}")
    
    # Number swapping / moving
    if full_num:
        combos.add(f"{u}:{full_num}{letters}")
        combos.add(f"{u}:{letters}{full_num}")
        combos.add(f"{u}:{full_num}")
        combos.add(f"{u}:{letters}")
    
    # Reverse segments (cedric905 → 905cedric)
    if len(u) > 3:
        for i in range(2, len(u) - 1):
            prefix = u[:i]
            suffix = u[i:]
            if any(c.isdigit() for c in prefix) or any(c.isdigit() for c in suffix):
                combos.add(f"{u}:{suffix}{prefix}")
                combos.add(f"{u}:{prefix}{suffix}")
    
    # Year / long number handling
    long_nums = re.findall(r'\d{4,}', u)
    for n in long_nums:
        combos.add(f"{u}:{n}{letters}")
        combos.add(f"{u}:{letters}{n}")
    
    # Extra common Roblox-style combos
    if letters:
        combos.add(f"{u}:{letters}123")
        combos.add(f"{u}:123{letters}")
        combos.add(f"{u}:{letters}11")
        combos.add(f"{u}:{letters}12")
    
    return sorted(list(combos))


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            usernames = data.get('usernames', [])
            
            result = {}
            total = 0
            
            for user in usernames:
                combos = generate_combos(user)
                result[user] = combos
                total += len(combos)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps({
                "status": "success",
                "combos": result,
                "total_generated": total,
                "users_processed": len(usernames)
            }).encode())
            
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
            "message": "POST /api/combos with {\"usernames\": [\"user1\", \"user2\", ...]}"
        }).encode())
