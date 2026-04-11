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


export function getArticleTextBlob(article) {
  return textBlob(article);
}

export function isLocalPillar(article) {
  const category = norm(article?.category);
  const section = norm(article?.section);
  const scope = norm(article?.scope);
  const location = norm(article?.location);
  const t = textBlob(article);

  if (category.includes("local")) return true;
  if (scope.includes("cheshire")) return true;
  if (scope === "local") return true;
  if (section.includes("local")) return true;
  if (location.includes("cheshire")) return true;

  return /\b(cheshire|chester|crewe|nantwich|wilmslow|knutsford|macclesfield|northwich|winsford|ellesmere\s+port|congleton|sandbach|middlewich|alderley\s+edge)\b/.test(t);
}

export function isBusinessPillar(article) {
  const category = norm(article?.category);
  const section = norm(article?.section);
  const t = textBlob(article);

  if (category === "business") return true;
  if (section === "business") return true;

  return /\b(company|companies|earnings|profit|profits|profit\s+warning|revenue|sales|trading\s+update|merger|acquisition|takeover|ceo|startup|funding\s+round|venture\s+capital|manufacturer|manufacturing|retailer|retail\s+sector|supply\s+chain|factory|industry)\b/.test(t);
}

export function isFinancePillar(article) {
  const category = norm(article?.category);
  const section = norm(article?.section);
  const t = textBlob(article);

  if (category.includes("finance")) return true;
  if (category.includes("money")) return true;
  if (category.includes("property")) return true;
  if (category.includes("tax")) return true;

  if (["money", "tax", "property", "mortgages", "housing", "planning"].includes(section)) return true;

  return /\b(mortgage|mortgages|remortgage|fixed\s*rate|tracker|interest\s*rate|rate\s*cut|rate\s*hike|isa|savings|credit\s*card|loan|debt|council\s*tax|stamp\s*duty|hmrc|tax|vat|rebate|refund|rent|rental|landlord|tenant|housing|property|planning)\b/.test(t);
}

export function isAiTechPillar(article) {
  const category = norm(article?.category);
  const section = norm(article?.section);

  if (section.startsWith("ai-")) return true;
  if (category.includes("ai")) return true;
  if (category.includes("tech")) return true;

  const t = textBlob(article);
  return /(?:\bai\b|artificial\s+intelligence|chatgpt|openai|gemini|\bllm\b|gpt-?\d*|\bprompt\b|machine\s*learning|deep\s*learning|neural|\bchip\b|\bgpu\b|nvidia|amd|intel|semiconductor|cybersecurity|ransomware|malware|phishing|hack(?:ed|ing)?|data\s*breach|\bbreach\b|cloud\s*comput(?:ing|e)|\bsaas\b|robot|automation)/i.test(t);
}

export function isUkPillar(article) {
  const category = norm(article?.category);
  const section = norm(article?.section);
  const scope = norm(article?.scope);

  if (category.includes("uk")) return true;
  if (["money", "tax", "property", "property & tax"].includes(category)) return true;
  if (section.includes("uk")) return true;
  if (scope === "uk") return true;

  return false;
}

export function getPrimaryPillar(article) {
  if (isLocalPillar(article)) return "Local";
  if (isUkPillar(article)) return "UK";
  if (isFinancePillar(article)) return "Finance";
  if (isBusinessPillar(article)) return "Business";
  if (isAiTechPillar(article)) return "AI & Tech";
  return "Local";
}

export function getDisplayCategoryForPillar(article) {
  const category = norm(article?.category);
  const section = norm(article?.section);

  if (category.includes("tax") || section === "tax") return "Tax";

  const pillar = getPrimaryPillar(article);
  if (pillar === "Local") return "Local News";
  if (pillar === "Business") return "Business";
  if (pillar === "AI & Tech") return "AI & Tech";
  if (pillar === "Finance") return "Finance";
  if (pillar === "UK") return "UK News";

  return article?.category || "Local News";
}
