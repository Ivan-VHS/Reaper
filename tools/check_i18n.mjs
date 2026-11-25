#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const fail = (message) => { console.error(`i18n: ${message}`); process.exitCode = 1; };
const readJson = async (path) => JSON.parse(await readFile(resolve(root, path), "utf8"));
const isRecord = (value) => value !== null && typeof value === "object" && !Array.isArray(value);

try {
  const manifest = await readJson("i18n/manifest.v1.json");
  const set = await readJson("i18n/catalogs.v1.json");

  if (manifest.schema !== "duck.i18n-manifest/v1") fail("unsupported manifest schema");
  if (set.schema !== "duck.i18n-catalog-set/v1") fail("unsupported catalog-set schema");
  if (manifest.sourceLocale !== set.sourceLocale) fail("source locale differs between manifest and catalog set");
  if (!manifest.languageTags?.acceptAnyWellFormedTag) fail("manifest must accept any well-formed BCP-47 tag");
  if (!Array.isArray(manifest.fallback) || manifest.fallback.at(-1) !== manifest.sourceLocale) {
    fail("fallback chain must end at the source locale");
  }

  const canonical = (tag) => {
    if (typeof tag !== "string" || !tag.trim()) throw new Error("empty locale tag");
    return Intl.getCanonicalLocales(tag)[0];
  };
  const source = set.locales?.[manifest.sourceLocale];
  if (!isRecord(source?.messages)) fail("source catalog has no messages object");
  const sourceKeys = Object.keys(source?.messages ?? {}).sort();
  if (sourceKeys.length === 0) fail("source catalog is empty");

  for (const [tag, entry] of Object.entries(manifest.catalogs ?? {})) {
    let canonicalTag;
    try { canonicalTag = canonical(tag); }
    catch { fail(`invalid BCP-47 tag: ${tag}`); continue; }
    if (canonicalTag !== tag) fail(`locale tag is not canonical: ${tag}; use ${canonicalTag}`);
    if (!isRecord(entry)) { fail(`manifest entry for ${tag} is invalid`); continue; }

    const bundle = set.locales?.[tag];
    if (!isRecord(bundle)) { fail(`catalog is missing for ${tag}`); continue; }
    if (bundle.name?.trim() === "" || !["ltr", "rtl"].includes(bundle.direction)) {
      fail(`catalog metadata is invalid for ${tag}`);
    }
    if (!isRecord(bundle.messages)) { fail(`messages object is missing for ${tag}`); continue; }

    const keys = Object.keys(bundle.messages).sort();
    for (const key of keys) {
      if (typeof bundle.messages[key] !== "string" || bundle.messages[key].trim() === "") {
        fail(`empty or non-string message: ${tag}:${key}`);
      }
      if (bundle.messages[key].includes("\uFFFD")) fail(`replacement character in ${tag}:${key}`);
    }
    if (entry.status === "complete") {
      const missing = sourceKeys.filter((key) => !Object.hasOwn(bundle.messages, key));
      const extra = keys.filter((key) => !Object.hasOwn(source.messages, key));
      if (missing.length || extra.length) fail(`${tag} is marked complete but key coverage differs (missing: ${missing.join(", ") || "none"}; extra: ${extra.join(", ") || "none"})`);
    }
    if (tag === manifest.sourceLocale && entry.status !== "source") fail("source locale must have status=source");
  }

  for (const tag of Object.keys(set.locales ?? {})) {
    try { canonical(tag); } catch { fail(`catalog set contains invalid locale tag: ${tag}`); }
    if (!Object.hasOwn(manifest.catalogs ?? {}, tag)) fail(`catalog ${tag} is not registered in manifest`);
  }

  if (typeof Intl.Segmenter !== "function") fail("runtime lacks Intl.Segmenter; grapheme-aware text editing cannot be verified");
  for (const tag of Object.keys(manifest.catalogs ?? {})) {
    try {
      new Intl.NumberFormat(tag).format(12345.67);
      new Intl.DateTimeFormat(tag).format(new Date("2026-01-02T03:04:05Z"));
      new Intl.PluralRules(tag).select(2);
    } catch (error) {
      fail(`Intl locale services failed for ${tag}: ${error.message}`);
    }
  }

  if (process.exitCode) process.exit(process.exitCode);
  console.log(`i18n: ${manifest.project} passed; ${Object.keys(manifest.catalogs).length} catalogs, ${sourceKeys.length} stable message ids; open BCP-47 tag policy enabled.`);
} catch (error) {
  fail(error.stack ?? String(error));
}
