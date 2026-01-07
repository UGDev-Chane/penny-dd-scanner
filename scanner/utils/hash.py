import hashlib, json
from pathlib import Path

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())

def sha256_json(obj) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True).encode("utf-8"))
