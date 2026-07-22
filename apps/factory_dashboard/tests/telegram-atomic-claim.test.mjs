import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { parentPort, isMainThread, Worker, workerData } from "node:worker_threads";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";

const STORE_PATH = fileURLToPath(new URL("../app/api/telegram-publications/store.ts", import.meta.url));
const TABLE_SQL = `CREATE TABLE telegram_publication_requests (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  status TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  message_text TEXT NOT NULL,
  affiliate_url TEXT NOT NULL,
  image_url TEXT NOT NULL,
  owner_approved INTEGER NOT NULL,
  link_preview_enabled INTEGER NOT NULL,
  telegram_message_id INTEGER,
  error TEXT NOT NULL,
  approved_at TEXT NOT NULL,
  claimed_at TEXT,
  sent_at TEXT,
  candidate_metadata TEXT NOT NULL DEFAULT '{}',
  authorization_kind TEXT NOT NULL DEFAULT 'manual',
  policy_id TEXT NOT NULL DEFAULT '',
  policy_version INTEGER NOT NULL DEFAULT 0,
  idempotency_key TEXT NOT NULL DEFAULT '',
  content_hash TEXT NOT NULL DEFAULT '',
  validation_snapshot_hash TEXT NOT NULL DEFAULT '',
  lease_token TEXT NOT NULL DEFAULT '',
  lease_expires_at TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
)`;

if (!isMainThread && workerData?.telegramClaimWorker) {
  const db = new DatabaseSync(workerData.dbPath);
  db.exec("PRAGMA busy_timeout = 5000");
  const control = new Int32Array(workerData.control);
  Atomics.add(control, 0, 1);
  Atomics.notify(control, 0);
  Atomics.wait(control, 1, 0);
  const rows = db.prepare(workerData.sql).all(...workerData.params);
  db.close();
  parentPort.postMessage(rows);
} else {
  const source = await readFile(STORE_PATH, "utf8");
  const sqlMatch = source.match(/const ATOMIC_TELEGRAM_CLAIM_SQL = `([\s\S]*?)`;/);
  assert.ok(sqlMatch, "The production atomic claim SQL must remain directly testable");
  const claimSql = sqlMatch[1];

  function timestamps() {
    const nowMs = Date.now();
    return {
      now: new Date(nowMs).toISOString(),
      earliest: new Date(nowMs - 2 * 60 * 60 * 1000).toISOString(),
      latest: new Date(nowMs + 5 * 60 * 1000).toISOString(),
      approved: new Date(nowMs - 60 * 1000).toISOString(),
      valid: new Date(nowMs + 60 * 60 * 1000).toISOString(),
      expired: new Date(nowMs - 60 * 1000).toISOString(),
    };
  }

  function insertPublication(db, values) {
    const time = timestamps();
    db.prepare(`INSERT INTO telegram_publication_requests (
      id, product_id, status, chat_id, message_text, affiliate_url, image_url,
      owner_approved, link_preview_enabled, telegram_message_id, error,
      approved_at, claimed_at, sent_at, candidate_metadata, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, '', ?, NULL, NULL, ?, ?, ?)`)
      .run(
        values.id,
        values.productId ?? `product-${values.id}`,
        values.status ?? "queued",
        "@achadosbaratosBrasil",
        `Oferta ${values.id}`,
        "https://meli.la/example",
        "https://http2.mlstatic.com/example.jpg",
        values.ownerApproved ?? 1,
        0,
        values.approvedAt ?? time.approved,
        JSON.stringify({ validUntil: values.validUntil ?? time.valid, idempotencyKey: values.idempotencyKey ?? `key-${values.id}` }),
        values.createdAt ?? time.approved,
        values.createdAt ?? time.approved,
      );
  }

  async function databaseWith(rows) {
    const directory = await mkdtemp(join(tmpdir(), "telegram-claim-"));
    const dbPath = join(directory, "queue.sqlite");
    const db = new DatabaseSync(dbPath);
    db.exec("PRAGMA journal_mode = WAL");
    db.exec(TABLE_SQL);
    for (const row of rows) insertPublication(db, row);
    db.close();
    return { directory, dbPath };
  }

  function waitForWorkers(control, count) {
    return new Promise((resolve, reject) => {
      const started = Date.now();
      const check = () => {
        if (Atomics.load(control, 0) === count) return resolve();
        if (Date.now() - started > 5000) return reject(new Error("Workers did not reach the claim barrier"));
        setTimeout(check, 5);
      };
      check();
    });
  }

  async function concurrentClaims(dbPath, workerCount = 2) {
    const time = timestamps();
    const leaseExpires = new Date(Date.now() + 5 * 60 * 1000).toISOString();
    const shared = new SharedArrayBuffer(Int32Array.BYTES_PER_ELEMENT * 2);
    const control = new Int32Array(shared);
    const workers = Array.from({ length: workerCount }, (_, index) => new Worker(new URL(import.meta.url), {
      workerData: {
        telegramClaimWorker: true,
        dbPath,
        sql: claimSql,
        params: [time.now, `lease-${index}`, leaseExpires, time.now, time.earliest, time.latest, time.now],
        control: shared,
      },
    }));
    const results = workers.map((worker) => new Promise((resolve, reject) => {
      worker.once("message", resolve);
      worker.once("error", reject);
      worker.once("exit", (code) => { if (code !== 0) reject(new Error(`Claim worker exited with ${code}`)); });
    }));
    await waitForWorkers(control, workerCount);
    Atomics.store(control, 1, 1);
    Atomics.notify(control, 1, workerCount);
    return Promise.all(results);
  }

  async function withQueue(rows, callback) {
    const fixture = await databaseWith(rows);
    try { return await callback(fixture.dbPath); }
    finally { await rm(fixture.directory, { recursive: true, force: true }); }
  }

  function inspect(dbPath, sql, ...params) {
    const db = new DatabaseSync(dbPath);
    const rows = db.prepare(sql).all(...params);
    db.close();
    return rows;
  }

  test("one queued publication is claimed by exactly one of two concurrent workers", async () => {
    await withQueue([{ id: "only" }], async (dbPath) => {
      const claims = await concurrentClaims(dbPath);
      assert.deepEqual(claims.map((rows) => rows.length).sort(), [0, 1]);
      assert.equal(inspect(dbPath, "SELECT count(*) AS total FROM telegram_publication_requests WHERE status = 'publishing'")[0].total, 1);
    });
  });

  test("two queued publications are claimed as different IDs by two concurrent workers", async () => {
    await withQueue([{ id: "first" }, { id: "second", createdAt: new Date(Date.now() - 30_000).toISOString() }], async (dbPath) => {
      const claims = await concurrentClaims(dbPath);
      const ids = claims.flat().map((row) => row.id);
      assert.equal(ids.length, 2);
      assert.equal(new Set(ids).size, 2);
    });
  });

  test("expired and non-queued publications are never claimed or mutated", async () => {
    const time = timestamps();
    const rows = [
      { id: "expired", validUntil: time.expired },
      { id: "pending", status: "pending_approval" },
      { id: "publishing", status: "publishing" },
      { id: "sent", status: "sent" },
    ];
    await withQueue(rows, async (dbPath) => {
      const claims = await concurrentClaims(dbPath);
      assert.deepEqual(claims.flat(), []);
      assert.deepEqual(
        inspect(dbPath, "SELECT id, status FROM telegram_publication_requests ORDER BY id")
          .map((row) => ({ id: row.id, status: row.status })),
        [
          { id: "expired", status: "queued" },
          { id: "pending", status: "pending_approval" },
          { id: "publishing", status: "publishing" },
          { id: "sent", status: "sent" },
        ],
      );
    });
  });

  test("repeating a claim for the same idempotency key cannot duplicate execution", async () => {
    await withQueue([{ id: "idempotent", idempotencyKey: "stable-key" }], async (dbPath) => {
      const first = await concurrentClaims(dbPath);
      const second = await concurrentClaims(dbPath);
      assert.equal(first.flat().length, 1);
      assert.equal(second.flat().length, 0);
      assert.equal(inspect(dbPath, "SELECT count(*) AS total FROM telegram_publication_requests")[0].total, 1);
    });
  });

  test("manual queued publications keep priority over autopilot delegation", () => {
    const match = source.match(/export async function claimTelegramPublication\(\) \{([\s\S]*?)\n\}/);
    assert.ok(match, "The public claim function must remain directly inspectable");
    const body = match[1];
    const existingQueueClaim = body.indexOf("claimNextQueuedPublication()");
    const delegation = body.indexOf("delegateOneAutopilotCandidate()");
    assert.ok(existingQueueClaim >= 0, "The worker checks the existing queue");
    assert.ok(delegation > existingQueueClaim, "Autopilot only delegates after the manual queue is empty");
    assert.match(body, /if \(existing\.items\.length\) return existing/);
  });
}
