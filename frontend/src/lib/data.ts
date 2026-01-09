import fs from "fs";
import path from "path";
import Papa from "papaparse";

const ARTIFACTS_DIR = path.join(process.cwd(), "..", "artifacts");
const DATA_DIR = path.join(process.cwd(), "..", "data");

export async function readCsv<T>(dir: string, filename: string): Promise<T[]> {
  const filePath = path.join(dir, filename);
  const content = fs.readFileSync(filePath, "utf8");
  return new Promise((resolve, reject) => {
    Papa.parse<T>(content, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => resolve(results.data),
      error: (error: Error) => reject(error),
    });
  });
}

export async function readJson<T>(dir: string, filename: string): Promise<T> {
  const filePath = path.join(dir, filename);
  const content = fs.readFileSync(filePath, "utf8");
  return JSON.parse(content);
}

export async function getClasses() {
  return readCsv<any>(DATA_DIR, "king_classes.csv");
}

export async function getCorpus() {
  return readCsv<any>(path.join(ARTIFACTS_DIR, "data"), "corpus.csv");
}

export async function getMatches() {
  return readCsv<any>(path.join(ARTIFACTS_DIR, "data"), "matches.csv");
}

export async function getConsistencyAnalysis() {
  return readCsv<any>(
    path.join(ARTIFACTS_DIR, "reports"),
    "consistency_analysis.csv"
  );
}

export async function getMatchCounts() {
  return readCsv<any>(
    path.join(ARTIFACTS_DIR, "reports"),
    "class_match_counts.csv"
  );
}

export async function getVerbCoverage() {
  return readJson<any>(
    path.join(ARTIFACTS_DIR, "reports"),
    "verb_coverage.json"
  );
}

export async function getNearMisses() {
  return readCsv<any>(
    path.join(ARTIFACTS_DIR, "reports"),
    "class_near_misses.csv"
  );
}
