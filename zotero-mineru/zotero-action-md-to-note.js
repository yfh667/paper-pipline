// Zotero Actions-and-Tags action: import mineru MD as a Zotero note.
//
// For each PDF attachment under the triggering (regular) item, locate the
// converted MD in C:\Users\Administrator\Zotero\mineru-mirror\<ATTACHMENT_KEY>\,
// convert markdown -> HTML, and either create or update a Zotero child note
// titled "Mineru MD: <pdf_stem>" under the same parent.
//
// Images: relative paths like ![](images/xxx.jpg) are rewritten to absolute
// file:// URLs pointing at the mirror directory, so figures render locally
// without bloating Zotero's sync storage with embedded base64 image data.
//
// Trigger only on regular items (with PDF children) or on a PDF attachment
// that has a parent. Standalone PDFs (no parent) are skipped — create a
// parent item first via Zotero's "Create Parent Item".
//
// Globals provided by Actions and Tags: item, items, Zotero, IOUtils, PathUtils.

const MIRROR_ROOT = String.raw`C:\Users\Administrator\Zotero\mineru-mirror`;
const NOTE_TITLE_PREFIX = "Mineru MD: ";

// ---------------------------------------------------------------------------
// Markdown -> HTML (small purpose-built converter; no external deps).
// Handles what mineru actually emits: ATX headings, paragraphs, fenced code,
// lists, bold/italic, inline code, images and links, blockquotes, hr.
// ---------------------------------------------------------------------------

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeAttr(s) {
  return escapeHtml(s).replace(/"/g, "&quot;");
}

function renderInline(text, imageBase) {
  // Order matters: images before links (image syntax is ![alt](src)).
  let out = escapeHtml(text);

  // Inline code: `code` (handle BEFORE other inline so backticks protect content)
  out = out.replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`);

  // Images: ![alt](src "title")
  out = out.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g, (_, alt, src, title) => {
    const absSrc = /^(?:[a-z]+:|\/|\\)/i.test(src)
      ? src
      : `file:///${imageBase.replace(/\\/g, "/")}/${src.replace(/\\/g, "/")}`;
    const titleAttr = title ? ` title="${escapeAttr(title)}"` : "";
    return `<img src="${escapeAttr(absSrc)}" alt="${escapeAttr(alt)}"${titleAttr}/>`;
  });

  // Links: [text](href)
  out = out.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g, (_, txt, href, title) => {
    const titleAttr = title ? ` title="${escapeAttr(title)}"` : "";
    return `<a href="${escapeAttr(href)}"${titleAttr}>${txt}</a>`;
  });

  // Bold + italic combined: ***text*** or ___text___
  out = out.replace(/(\*\*\*|___)(.+?)\1/g, "<strong><em>$2</em></strong>");
  // Bold: **text** or __text__
  out = out.replace(/(\*\*|__)(.+?)\1/g, "<strong>$2</strong>");
  // Italic: *text* or _text_
  out = out.replace(/(?<![*_\w])(\*|_)([^*_\n]+)\1(?![*_\w])/g, "<em>$2</em>");

  return out;
}

function mdToHtml(md, imageBase) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0;

  function flushParagraph(buf) {
    if (buf.length === 0) return;
    const text = buf.join("\n").trim();
    if (text) out.push(`<p>${renderInline(text, imageBase)}</p>`);
    buf.length = 0;
  }

  let paraBuf = [];

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    const fence = /^```(\w*)\s*$/.exec(line);
    if (fence) {
      flushParagraph(paraBuf);
      const lang = fence[1] || "";
      i++;
      const codeLines = [];
      while (i < lines.length && !/^```\s*$/.test(lines[i])) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing fence
      const langAttr = lang ? ` class="language-${escapeAttr(lang)}"` : "";
      out.push(`<pre><code${langAttr}>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
      continue;
    }

    // ATX heading: #..###### + space + text
    const heading = /^(#{1,6})\s+(.*?)\s*#*\s*$/.exec(line);
    if (heading) {
      flushParagraph(paraBuf);
      const level = heading[1].length;
      out.push(`<h${level}>${renderInline(heading[2], imageBase)}</h${level}>`);
      i++;
      continue;
    }

    // Horizontal rule
    if (/^\s*(?:-\s*){3,}$|^\s*(?:\*\s*){3,}$|^\s*(?:_\s*){3,}$/.test(line)) {
      flushParagraph(paraBuf);
      out.push("<hr/>");
      i++;
      continue;
    }

    // Blockquote
    if (/^>\s?/.test(line)) {
      flushParagraph(paraBuf);
      const quoteLines = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        quoteLines.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      out.push(`<blockquote>${renderInline(quoteLines.join("\n"), imageBase)}</blockquote>`);
      continue;
    }

    // Unordered list
    if (/^\s*[-*+]\s+/.test(line)) {
      flushParagraph(paraBuf);
      const items = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*+]\s+/, ""));
        i++;
      }
      out.push("<ul>" + items.map(t => `<li>${renderInline(t, imageBase)}</li>`).join("") + "</ul>");
      continue;
    }

    // Ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      flushParagraph(paraBuf);
      const items = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      out.push("<ol>" + items.map(t => `<li>${renderInline(t, imageBase)}</li>`).join("") + "</ol>");
      continue;
    }

    // Blank line -> paragraph break
    if (line.trim() === "") {
      flushParagraph(paraBuf);
      i++;
      continue;
    }

    // Default: accumulate into a paragraph
    paraBuf.push(line);
    i++;
  }
  flushParagraph(paraBuf);

  return out.join("\n");
}

// ---------------------------------------------------------------------------
// Mirror lookup
// ---------------------------------------------------------------------------

async function findMdFile(dirPath) {
  let best = null;
  let bestSize = -1;
  async function walk(d) {
    let entries;
    try { entries = await IOUtils.getChildren(d); }
    catch (e) { return; }
    for (const p of entries) {
      let info;
      try { info = await IOUtils.stat(p); } catch (e) { continue; }
      if (info.type === "directory") { await walk(p); }
      else if (p.toLowerCase().endsWith(".md")) {
        if (info.size > bestSize) { bestSize = info.size; best = p; }
      }
    }
  }
  await walk(dirPath);
  return best;
}

// ---------------------------------------------------------------------------
// Per-attachment processing
// ---------------------------------------------------------------------------

async function importMdForAttachment(parentItem, pdfAttachment) {
  const key = pdfAttachment.key;
  const mirrorDir = PathUtils.join(MIRROR_ROOT, key);
  if (!(await IOUtils.exists(mirrorDir))) return `[${key}] no mirror yet`;

  const mdPath = await findMdFile(mirrorDir);
  if (!mdPath) return `[${key}] no md found in mirror`;

  // The folder that holds the MD also holds the images/ dir mineru produced.
  const mdParts = mdPath.split(/[\\/]/);
  mdParts.pop();
  const imageBase = mdParts.join("/");
  const pdfStem = pdfAttachment.attachmentFilename
    ? pdfAttachment.attachmentFilename.replace(/\.pdf$/i, "")
    : key;
  const noteTitle = NOTE_TITLE_PREFIX + pdfStem;

  // Look for an existing note under the same parent with the same title.
  let existingNote = null;
  for (const childID of parentItem.getNotes()) {
    const n = await Zotero.Items.getAsync(childID);
    if (!n) continue;
    const t = (n.getNoteTitle && n.getNoteTitle()) || "";
    if (t === noteTitle) { existingNote = n; break; }
  }

  const mdText = await IOUtils.readUTF8(mdPath);
  const bodyHtml = mdToHtml(mdText, imageBase);
  // Zotero notes need a title block; Zotero derives note title from the
  // first heading or first line. Embed title as h1.
  const fullHtml = `<h1>${escapeHtml(noteTitle)}</h1>\n${bodyHtml}`;

  if (existingNote) {
    existingNote.setNote(fullHtml);
    await existingNote.saveTx();
    return `[${key}] UPDATED note ${existingNote.key} (${mdText.length} chars)`;
  }

  const newNote = new Zotero.Item("note");
  newNote.parentID = parentItem.id;
  newNote.setNote(fullHtml);
  await newNote.saveTx();
  return `[${key}] CREATED note ${newNote.key} (${mdText.length} chars, md=${mdPath})`;
}

// ---------------------------------------------------------------------------
// Entrypoint
// ---------------------------------------------------------------------------

async function processOne(target) {
  // Resolve to the regular parent item.
  let parent = target;
  if (target.isAttachment()) {
    if (!target.parentItemID) {
      return `[${target.key}] skipped: standalone attachment has no parent — Create Parent Item first`;
    }
    parent = await Zotero.Items.getAsync(target.parentItemID);
  }
  if (!parent.isRegularItem()) {
    return `[${parent.key}] skipped: not a regular item`;
  }

  const results = [];
  for (const attID of parent.getAttachments()) {
    const att = await Zotero.Items.getAsync(attID);
    if (att.attachmentContentType !== "application/pdf") continue;
    results.push(await importMdForAttachment(parent, att));
  }
  return results.length ? results.join("\n") : `[${parent.key}] no PDF children`;
}

const targets = (typeof items !== "undefined" && items && items.length) ? items : [item];
const summary = [];
for (const t of targets) {
  try { summary.push(await processOne(t)); }
  catch (e) { summary.push(`error on ${t && t.key ? t.key : "?"}: ${e.message}\n${e.stack || ""}`); }
}
return summary.join("\n");
