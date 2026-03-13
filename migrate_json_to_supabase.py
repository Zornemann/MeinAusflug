import os
import json
import psycopg

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    raise RuntimeError("SUPABASE_DB_URL ist nicht gesetzt.")

# SSL sicherstellen
if "sslmode=" not in DB_URL:
    DB_URL += ("&" if "?" in DB_URL else "?") + "sslmode=require"

JSON_PATH = os.path.join("data", "reisen_daten.json")  # ggf. anpassen

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

payload = json.dumps(data, ensure_ascii=False)

with psycopg.connect(DB_URL) as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into app_state (id, data, updated_at)
            values (1, %s::jsonb, now())
            on conflict (id) do update
              set data = excluded.data,
                  updated_at = now();
            """,
            (payload,),
        )
    conn.commit()

print("✅ Migration fertig: lokale JSON nach Supabase app_state übertragen.")