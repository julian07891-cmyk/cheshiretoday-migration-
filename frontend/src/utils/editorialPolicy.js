/**
 * Editorial policy (Site-wide)
 * Goal: Hide "crime-only" content everywhere EXCEPT when explicitly overridden.
 *
 * Override signals (any true => allow):
 * - article.featured === true
 * - article.is_priority_cheshire === true
 * - article.tags includes "editorial:allow" or "allow_crime"
 *
 * Public-interest exceptions (allowed even if crime-like):
 * - Major disruption / safety / essential services: road/rail closures, severe weather, outages
 * - Missing-person / public appeals
 */

export function hasEditorialOverride(article) {
  if (!article) return false;

  if (article.featured === true) return true;
  if (article.is_priority_cheshire === true) return true;

  const tags = Array.isArray(article.tags) ? article.tags : [];
  const tagStr = tags.map(String).map((t) => t.toLowerCase());
  if (tagStr.includes("editorial:allow")) return true;
  if (tagStr.includes("allow_crime")) return true;

  return false;
}

function norm(s) {
  return String(s || "").toLowerCase();
}

function textBlob(article) {
  const title = norm(article?.title);
  const summary = norm(article?.summary);
  const content = norm(article?.content);
  return `${title} ${summary} ${content}`.trim();
}

export function isPublicInterestException(article) {
  if (!article) return false;
  const t = textBlob(article);

  if (/\b(storm|flood|flooding|severe\s+weather|met\s+office|amber\s+warning|red\s+warning|power\s+cut|outage|blackout)\b/.test(t)) return true;
  if (/\b(road|motorway|a\d{2,4}|m\d|rail|train|bus|bridge|closure|closed|shut|blocked|diversion|traffic|delays?)\b/.test(t)) return true;
  if (/\b(missing\s+person|appeal\s+for\s+information|public\s+appeal)\b/.test(t)) return true;

  return false;
}

/**
 * Crime-like detection (tightened):
 * - Violent/sexual crime => always crime-like
 * - Criminal justice / policing / sentencing signals => crime-like
 * - Fraud/scam => crime-like ONLY if paired with justice signals (charged/jailed/court/police etc.)
 *
 * This avoids false positives like “FedEx sues … tariff refund” or general “tariff policy” coverage.
 */
export function isCrimeLike(article) {
  if (!article) return false;

  // Publisher labeling
  const category = norm(article.category);
  const section = norm(article.section);
  const scope = norm(article.scope);
  const catBlob = `${category} ${section} ${scope}`;

  // If a publisher explicitly labels it crime/police/court -> treat as crime-like
  if (catBlob.includes("crime")) return true;
  if (catBlob.includes("police")) return true;
  if (catBlob.includes("court")) return true;

  const t = textBlob(article);

  // 1) Hard violent/sexual crime vocabulary (always crime-like)
  const violentRe =
    /\b(stab(?:bed|bing)?|shoot(?:ing)?|murder|manslaughter|rape|sexual\s+assault|paedophile|child\s+abuse|domestic\s+abuse)\b/;

  // 2) Criminal justice / policing signals (crime-like)
  const justiceRe =
    /\b(arrest(?:ed)?|charged|bail|police|officer|pcso|raid|warrant|investigation|suspect|victim|magistrates|crown\s+court|court|trial|plead(?:ed)?|guilty|not\s+guilty|sentenc(?:ed|ing)|custody|prison|jailed)\b/;

  // 3) Property crime / weapons (crime-like)
  const crimeRe =
    /\b(assault|robbery|burglary|theft|stolen|knife\s+crime|weapon|gun|firearm)\b/;

  // 4) Fraud/scam (ONLY crime-like if paired with justice signals)
  const fraudRe =
    /\b(fraud|scam|money\s+launder(?:ing|ed))\b/;

  if (violentRe.test(t)) return true;
  if (justiceRe.test(t)) return true;
  if (crimeRe.test(t)) return true;

  // Fraud/scam needs a justice context to be treated as crime
  if (fraudRe.test(t) && justiceRe.test(t)) return true;

  return false;
}

export function passesEditorialPolicy(article) {
  if (hasEditorialOverride(article)) return true;
  if (isPublicInterestException(article)) return true;
  return !isCrimeLike(article);
}

export function filterEditorialPool(list) {
  const arr = Array.isArray(list) ? list : [];
  return arr.filter(passesEditorialPolicy);
}
