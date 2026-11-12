"""Durable conversations, task snapshots and summaries; no graph execution."""
import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS agent_runs (id TEXT PRIMARY KEY, conversation TEXT NOT NULL, body TEXT NOT NULL)')
        self.db.execute('CREATE INDEX IF NOT EXISTS agent_conversation ON agent_runs(conversation)')
        self.db.execute('CREATE TABLE IF NOT EXISTS agent_conversations (id TEXT PRIMARY KEY, deleting INTEGER NOT NULL DEFAULT 0)')
        self.db.execute('CREATE TABLE IF NOT EXISTS agent_summaries (conversation TEXT PRIMARY KEY, body TEXT NOT NULL)')
        self.db.commit()

    def get(self, run_id):
        row = self.db.execute('SELECT body FROM agent_runs WHERE id=?', (run_id,)).fetchone()
        if row is None: raise KeyError(run_id)
        return json.loads(row[0])

    def put(self, run):
        run['version'] = run.get('version', 0) + 1
        # Keep creation order stable when an older task is retried or updated.
        self.db.execute('INSERT INTO agent_runs VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                        (run['id'], run['conversation_id'], json.dumps(run, ensure_ascii=False)))
        self.db.commit()
        return run

    def update(self, run_id, **fields):
        return self.put({**self.get(run_id), **fields})

    def conversation(self, conversation):
        return [json.loads(r[0]) for r in self.db.execute(
            'SELECT body FROM agent_runs WHERE conversation=? ORDER BY rowid', (conversation,))]

    def create_conversation(self, conversation):
        self.db.execute('INSERT INTO agent_conversations(id) VALUES (?)', (conversation,))
        self.db.commit()

    def conversation_status(self, conversation):
        row = self.db.execute('SELECT deleting FROM agent_conversations WHERE id=?', (conversation,)).fetchone()
        return None if row is None else ('deleting' if row[0] else 'active')

    def mark_deleting(self, conversation):
        self.db.execute('UPDATE agent_conversations SET deleting=1 WHERE id=?', (conversation,))
        self.db.commit()

    def remove_conversation(self, conversation):
        self.db.execute('DELETE FROM agent_runs WHERE conversation=?', (conversation,))
        self.db.execute('DELETE FROM agent_summaries WHERE conversation=?', (conversation,))
        self.db.execute('DELETE FROM agent_conversations WHERE id=?', (conversation,))
        self.db.commit()

    def summary(self, conversation):
        row = self.db.execute('SELECT body FROM agent_summaries WHERE conversation=?', (conversation,)).fetchone()
        return json.loads(row[0]) if row else {'data': {}, 'covered': []}

    def save_summary(self, conversation, value):
        self.db.execute('INSERT OR REPLACE INTO agent_summaries VALUES (?,?)', (conversation, json.dumps(value, ensure_ascii=False)))
        self.db.commit()

    def conversations(self):
        return [r[0] for r in self.db.execute('SELECT id FROM agent_conversations')]

    def runs(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT body FROM agent_runs').fetchall()]

    def close(self):
        self.db.close()
