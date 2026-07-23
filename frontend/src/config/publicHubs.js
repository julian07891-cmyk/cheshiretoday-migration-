export const CATEGORY_HUBS = [
  {
    slug: "local-news",
    label: "Local",
    canonicalCategory: "Local News",
    aliases: ["Local"],
    title: "Local news and updates",
    description: "Latest local reporting from across Cheshire and its communities.",
  },
  {
    slug: "uk-news",
    label: "UK",
    canonicalCategory: "UK News",
    aliases: ["UK"],
    title: "UK news and updates",
    description: "Important UK news and developments affecting Cheshire readers.",
  },
  {
    slug: "business",
    label: "Business",
    canonicalCategory: "Business",
    aliases: ["Economy", "Economic"],
    title: "Business news and updates",
    description: "Cheshire business, investment, jobs and economic news.",
  },
  {
    slug: "finance",
    label: "Finance",
    canonicalCategory: "Finance",
    aliases: ["Tax", "Property", "Property & Tax", "Money"],
    title: "Finance news and updates",
    description: "Personal finance, tax, markets and money news for Cheshire readers.",
  },
  {
    slug: "ai-tech",
    label: "AI & Tech",
    canonicalCategory: "AI & Tech",
    aliases: ["AI", "Tech", "Technology"],
    title: "AI & Tech news and updates",
    description: "Practical artificial intelligence and technology coverage.",
  },
];

export const LOCATION_HUBS = [
  { slug: "cheshire-general", name: "Cheshire", description: "Latest news and updates from across Cheshire." },
  { slug: "chester", name: "Chester", description: "Latest news from Chester, Ellesmere Port and surrounding areas." },
  { slug: "warrington", name: "Warrington", description: "Latest news from Warrington, Lymm, Culcheth and surrounding areas." },
  { slug: "crewe", name: "Crewe", description: "Latest news from Crewe, Nantwich, Sandbach and South Cheshire." },
  { slug: "macclesfield", name: "Macclesfield", description: "Latest news from Macclesfield, Congleton, Bollington and East Cheshire." },
  { slug: "wilmslow", name: "Wilmslow", description: "Latest news from Wilmslow, Handforth, Styal and surrounding areas." },
  { slug: "knutsford", name: "Knutsford", description: "Latest news from Knutsford, Tatton and surrounding areas." },
  { slug: "northwich", name: "Northwich", description: "Latest news from Northwich, Winsford, Middlewich and Mid Cheshire." },
];

export const findCategoryHub = (slug) =>
  CATEGORY_HUBS.find((hub) => hub.slug === String(slug || "").toLowerCase());

export const findLocationHub = (slug) =>
  LOCATION_HUBS.find((hub) => hub.slug === String(slug || "").toLowerCase());
