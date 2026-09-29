import JSZip from "jszip";

/** Upload limit shared with the backend (MAX_ZIP_SIZE). */
export const MAX_ZIP_BYTES = 100 * 1024 * 1024;

/** Raw folder size guard before compression (zip-bomb-ish folders). */
const MAX_RAW_FOLDER_BYTES = 500 * 1024 * 1024;

/** Same ignore list as the backend (analyzer/utils.py). */
const IGNORED_DIRS = new Set([
  ".git",
  "node_modules",
  "venv",
  ".venv",
  "__pycache__",
  "dist",
  "build",
  "target",
  ".idea",
  ".vscode",
  "coverage",
  ".cache",
]);

export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) {
    const kb = bytes / 1024;
    return Number.isInteger(kb) ? `${kb} KB` : `${kb.toFixed(1)} KB`;
  }
  const mb = bytes / (1024 * 1024);
  if (mb < 1024) return Number.isInteger(mb) ? `${mb} MB` : `${mb.toFixed(2)} MB`;
  return `${(mb / 1024).toFixed(2)} GB`;
}

/**
 * Compress a folder selection into a project.zip entirely in the browser,
 * preserving the folder structure (webkitRelativePath).
 */
export async function zipFolderFiles(files: File[]): Promise<File> {
  if (files.length === 0) {
    throw new Error("No files selected.");
  }

  const zip = new JSZip();
  let rawSize = 0;
  let added = 0;
  let rootName = "";

  for (const file of files) {
    const relative =
      (file as File & { webkitRelativePath?: string }).webkitRelativePath ||
      file.name;
    const parts = relative.split("/");
    // Skip ignored folders (node_modules, .git, dist, ...) like the backend does.
    if (parts.some((part) => IGNORED_DIRS.has(part))) {
      continue;
    }
    if (!rootName && relative.includes("/")) {
      rootName = parts[0];
    }
    rawSize += file.size;
    if (rawSize > MAX_RAW_FOLDER_BYTES) {
      throw new Error("Selected folder is too large (500 MB limit).");
    }
    zip.file(relative, file);
    added += 1;
  }

  if (added === 0) {
    throw new Error(
      "All selected files were inside ignored folders (node_modules, .git, dist, ...).",
    );
  }

  const blob = await zip.generateAsync({ type: "blob" });
  if (blob.size > MAX_ZIP_BYTES) {
    throw new Error(
      `Compressed folder is ${formatSize(blob.size)} — the upload limit is ${formatSize(
        MAX_ZIP_BYTES,
      )}.`,
    );
  }
  return new File([blob], `${rootName || "project"}.zip`, {
    type: "application/zip",
  });
}
