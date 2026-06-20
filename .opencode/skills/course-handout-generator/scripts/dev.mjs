#!/usr/bin/env node

import { watch, existsSync } from "fs";
import { join } from "path";
import { createServer } from "http";
import { execSync } from "child_process";

const courseDir = process.argv[2] || ".";
const port = parseInt(process.argv.find(a => a.startsWith("--port="))?.split("=")[1] || "3000");

function build() {
  try {
    const script = join(import.meta.dirname, "build.mjs");
    execSync(`node "${script}" "${courseDir}"`, { stdio: "inherit" });
  } catch { /* errors printed by build.mjs */ }
}

// Initial build
build();

// Watch
const watchPaths = [
  join(courseDir, "content.md"),
  join(courseDir, "config.yaml"),
  join(process.env.HOME || process.env.USERPROFILE || ".", ".config", "opencode", "skills", "course-handout-generator", "config", "global.yaml"),
  join(import.meta.dirname, "..", "reference", "base.html"),
];

watchPaths.forEach(p => {
  if (existsSync(p)) {
    watch(p, () => {
      console.log(`\n🔁 Change detected: ${p}`);
      build();
    });
  }
});

// Server
const distDir = join(courseDir, "dist");
createServer((req, res) => {
  const filePath = req.url === "/" ? join(distDir, "index.html") : join(distDir, req.url);
  if (existsSync(filePath)) {
    const ext = filePath.split(".").pop();
    const mime = { html: "text/html", css: "text/css", js: "application/javascript", png: "image/png", jpg: "image/jpeg", svg: "image/svg+xml" };
    res.writeHead(200, { "Content-Type": mime[ext] || "text/plain" });
    require("fs").createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404);
    res.end("Not found");
  }
}).listen(port, () => {
  console.log(`\n🌐 http://localhost:${port}`);
  console.log("  Watching for changes...\n");
});
