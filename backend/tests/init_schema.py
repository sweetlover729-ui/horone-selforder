"""Initialize test database schema from schema.sql.

Uses psql (postgresql-client) for reliable pg_dump import, handling
multi-statement SQL, $$-quoted function bodies, etc.
"""
import subprocess
import sys
import os

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/test_selforder",
)
schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

# Parse DB_URL into psql arguments
# Format: postgresql://user:password@host:port/dbname
import urllib.parse
parsed = urllib.parse.urlparse(DB_URL)

env = os.environ.copy()
if parsed.password:
    env["PGPASSWORD"] = parsed.password

cmd = [
    "psql",
    "-h", parsed.hostname or "localhost",
    "-p", str(parsed.port or 5432),
    "-U", parsed.username or "postgres",
    "-d", parsed.path.lstrip("/") or "test_selforder",
    "-f", schema_path,
    "-v", "ON_ERROR_STOP=1",
    "-q",
]

result = subprocess.run(cmd, env=env, capture_output=True, text=True)
if result.returncode != 0:
    print("Schema init FAILED:", file=sys.stderr)
    print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)

print("Schema created successfully")
