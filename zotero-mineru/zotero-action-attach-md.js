// Zotero "Actions and Tags" action: attach mineru-converted MD files as
// linked child attachments. Requires the target to be a regular bibliographic
// item (with PDF child attachments) or a PDF attachment that already has a
// parent item. Standalone PDFs (no parent) are skipped — create a parent
// item via Zotero's "Create Parent Item" first.
//
// Globals: item, items, Zotero, IOUtils, PathUtils.

const MIRROR_ROOT = String.raw`C:\Users\Administrator\Zotero\mineru-mirror`;
const MD_TITLE = "Mineru MD";

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

async function attachMdForItem(targetItem) {
  if (!targetItem || targetItem.isAttachment()) {
    return { skipped: true, reason: "not a regular item" };
  }
  const attIDs = targetItem.getAttachments();
  const results = [];
  for (const attID of attIDs) {
    const att = await Zotero.Items.getAsync(attID);
    if (att.attachmentContentType !== "application/pdf") continue;
    const key = att.key;
    const mirrorDir = PathUtils.join(MIRROR_ROOT, key);
    if (!(await IOUtils.exists(mirrorDir))) {
      results.push(`[${key}] no mirror yet`);
      continue;
    }
    const mdPath = await findMdFile(mirrorDir);
    if (!mdPath) {
      results.push(`[${key}] no md found in mirror`);
      continue;
    }

    let already = false;
    for (const childID of targetItem.getAttachments()) {
      const c = await Zotero.Items.getAsync(childID);
      if (c.attachmentLinkMode === Zotero.Attachments.LINK_MODE_LINKED_FILE
          && c.attachmentPath
          && c.attachmentPath.toLowerCase() === mdPath.toLowerCase()) {
        already = true;
        break;
      }
    }
    if (already) { results.push(`[${key}] already attached`); continue; }

    await Zotero.Attachments.linkFromFile({
      file: mdPath,
      parentItemID: targetItem.id,
      contentType: "text/markdown",
      title: MD_TITLE,
    });
    results.push(`[${key}] linked ${mdPath}`);
  }
  return { skipped: false, results };
}

const targets = (typeof items !== "undefined" && items && items.length) ? items : [item];
const summary = [];
for (const t of targets) {
  try {
    let parent = t;
    if (t.isAttachment() && t.parentItemID) {
      parent = await Zotero.Items.getAsync(t.parentItemID);
    }
    const r = await attachMdForItem(parent);
    if (r.skipped) summary.push(`skip ${parent.key}: ${r.reason}`);
    else summary.push(`${parent.key}: ${r.results.join(" | ") || "(no pdf children)"}`);
  } catch (e) {
    summary.push(`error on ${t.key}: ${e.message}`);
  }
}
return summary.join("\n");
