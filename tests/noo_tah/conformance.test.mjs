import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createHash, randomBytes } from "node:crypto";
import { createServer, get } from "node:http";
import { createServer as createTcpServer, connect } from "node:net";
import { lookup } from "node:dns/promises";
import { Readable, Transform, Writable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { Worker } from "node:worker_threads";
import { spawnSync } from "node:child_process";
import { setImmediate as immediate } from "node:timers/promises";

test("Node runtime exposes versioned V8, libuv and N-API metadata", () => {
  assert.match(process.version, /^v\d+\./);
  assert.ok(process.versions.v8);
  assert.ok(process.versions.uv);
  assert.ok(process.versions.napi);
  assert.ok(["win32", "linux", "darwin"].includes(process.platform));
});

test("ESM and CommonJS module systems both execute", () => {
  assert.equal(typeof import.meta.url, "string");
  const result = spawnSync(process.execPath, [
    "-e",
    "const fs = require('node:fs'); if (!fs.readFileSync) process.exit(4); process.stdout.write('CJS_OK')",
  ], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, "CJS_OK");
});

test("filesystem promises read and write binary data without blocking the test", async () => {
  const directory = await mkdtemp(join(tmpdir(), "noo-tah-"));
  const file = join(directory, "payload.bin");
  const payload = randomBytes(128 * 1024);
  try {
    await writeFile(file, payload);
    assert.deepEqual(await readFile(file), payload);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("crypto hashes binary buffers deterministically", () => {
  const digest = createHash("sha256").update("NOO TAH").digest("hex");
  assert.equal(digest.length, 64);
  assert.equal(createHash("sha256").update("NOO TAH").digest("hex"), digest);
  assert.equal(randomBytes(32).length, 32);
});

test("streams pipeline chunks with bounded writable buffering", async () => {
  let count = 0;
  let output = "";
  const source = Readable.from(Array.from({ length: 40 }, (_, i) => String(i) + ","));
  const transform = new Transform({
    transform(chunk, _encoding, callback) {
      count += 1;
      callback(null, chunk.toString().toUpperCase());
    },
  });
  const sink = new Writable({
    highWaterMark: 1,
    write(chunk, _encoding, callback) {
      output += chunk.toString();
      setTimeout(callback, 1);
    },
  });
  await pipeline(source, transform, sink);
  assert.equal(count, 40);
  assert.equal(output, Array.from({ length: 40 }, (_, i) => String(i) + ",").join(""));
});

test("HTTP server and client exchange data on loopback", async () => {
  const server = createServer((request, response) => {
    response.writeHead(200, { "content-type": "text/plain" });
    response.end("NOO_TAH:" + request.url);
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  try {
    const address = server.address();
    assert.ok(address && typeof address === "object");
    const body = await new Promise((resolve, reject) => {
      const request = get("http://127.0.0.1:" + address.port + "/health", (response) => {
        let value = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => { value += chunk; });
        response.on("end", () => resolve(value));
      });
      request.once("error", reject);
    });
    assert.equal(body, "NOO_TAH:/health");
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
});

test("TCP sockets transfer bytes and close cleanly", async () => {
  const server = createTcpServer((socket) => socket.end("TCP_OK"));
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  try {
    const address = server.address();
    assert.ok(address && typeof address === "object");
    const received = await new Promise((resolve, reject) => {
      const socket = connect(address.port, "127.0.0.1");
      let data = "";
      socket.setEncoding("utf8");
      socket.on("data", (chunk) => { data += chunk; });
      socket.once("end", () => resolve(data));
      socket.once("error", reject);
    });
    assert.equal(received, "TCP_OK");
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
});

test("worker_threads execute CPU work in an isolated worker", async () => {
  const worker = new Worker(
    "const { parentPort, workerData } = require('node:worker_threads'); parentPort.postMessage(workerData * workerData)",
    { eval: true, workerData: 12 },
  );
  const result = await new Promise((resolve, reject) => {
    worker.once("message", resolve);
    worker.once("error", reject);
    worker.once("exit", (code) => {
      if (code !== 0) reject(new Error("worker exited with " + code));
    });
  });
  assert.equal(result, 144);
});

test("child_process executes a separate Node process and preserves exit status", () => {
  const child = spawnSync(process.execPath, ["-e", "process.stdout.write('CHILD_OK'); process.exitCode = 7"], {
    encoding: "utf8",
    timeout: 5000,
  });
  assert.equal(child.status, 7);
  assert.equal(child.stdout, "CHILD_OK");
});

test("DNS resolver resolves localhost without external network access", async () => {
  const result = await lookup("localhost");
  assert.ok(result.family === 4 || result.family === 6);
  assert.ok(result.address === "127.0.0.1" || result.address === "::1");
});

test("event loop drains nextTick and promise microtasks before immediate callbacks", async () => {
  const order = [];
  process.nextTick(() => order.push("nextTick"));
  Promise.resolve().then(() => order.push("promise"));
  await immediate();
  assert.deepEqual(order, ["nextTick", "promise"]);
});
