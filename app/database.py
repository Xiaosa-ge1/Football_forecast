import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "worldcup.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            home TEXT NOT NULL,
            away TEXT NOT NULL,
            venue TEXT DEFAULT '',
            status TEXT DEFAULT '未开始',
            home_score INTEGER,
            away_score INTEGER,
            events_json TEXT DEFAULT '[]',
            home_lineup_json TEXT DEFAULT '[]',
            away_lineup_json TEXT DEFAULT '[]',
            stats_json TEXT DEFAULT '{}',
            referee TEXT DEFAULT '',
            attendance TEXT DEFAULT '',
            weather_json TEXT DEFAULT '{}',
            source TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date);
        CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);

        CREATE TABLE IF NOT EXISTS standings (
            team TEXT NOT NULL,
            group_name TEXT NOT NULL,
            played INTEGER DEFAULT 0,
            won INTEGER DEFAULT 0,
            drawn INTEGER DEFAULT 0,
            lost INTEGER DEFAULT 0,
            goals_for INTEGER DEFAULT 0,
            goals_against INTEGER DEFAULT 0,
            goal_diff INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            rank INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (team, group_name)
        );

        CREATE TABLE IF NOT EXISTS injuries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            player TEXT NOT NULL,
            injury_type TEXT DEFAULT '',
            severity TEXT DEFAULT '',
            expected_return TEXT DEFAULT '',
            source TEXT DEFAULT '',
            reported_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_injuries_team ON injuries(team);

        CREATE TABLE IF NOT EXISTS crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            fetched_at TEXT DEFAULT (datetime('now')),
            matches_count INTEGER DEFAULT 0,
            standings_count INTEGER DEFAULT 0,
            injuries_count INTEGER DEFAULT 0,
            success INTEGER DEFAULT 1,
            error_message TEXT
        );
    """)
    conn.commit()
    conn.close()
