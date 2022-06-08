import * as path from "path";
import { buildSync } from "esbuild";

buildSync({
    entryPoints: [process.env.ENTRY_POINT],
    platform: "node",
    target: "es2018",
    bundle: true,
    format: "cjs",
    sourcemap: "external",
    outdir: "dist",
    absWorkingDir: process.env.WORKING_DIRECTORY,
  });
    
console.log(path.join(process.env.WORKING_DIRECTORY, "dist"))