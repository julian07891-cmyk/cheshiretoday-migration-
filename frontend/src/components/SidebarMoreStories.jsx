import React, { useEffect, useState } from "react";
import { getApiUrl } from "../utils/api";
import { Clock } from "lucide-react";

function formatDate(dateString) {
  if (!dateString) return "";
  const d = new Date(dateString);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export default function SidebarMoreStories({ currentId, limit = 6, title = "More stories" }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        const API = getApiUrl().replace(/\/$/, "");
        const res = await fetch(`${API}/api/articles?limit=${Math.max(limit + 6, 12)}`);
        const data = await res.json();

        const arr = Array.isArray(data)
          ? data
          : Array.isArray(data?.articles)
          ? data.articles
          : [];

        const filtered = arr
          .filter((a) => (a?.id || a?._id) && String(a.id || a._id) !== String(currentId || ""))
          .slice(0, limit);

        if (mounted) setItems(filtered);
      } catch (e) {
        if (mounted) setItems([]);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, [currentId, limit]);

  if (loading) {
    return (
      <div className="rounded-xl border border-[#E6E1D8] bg-[#FBFAF7] p-4">
        <div className="h-4 w-32 bg-black/10 rounded mb-3 animate-pulse" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-4 bg-black/10 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!items || items.length === 0) return null;

  return (
    <section className="rounded-xl border border-[#E6E1D8] bg-[#FBFAF7] p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-extrabold tracking-tight text-neutral-900">{title}</h3>
        <span className="text-[11px] px-2 py-1 rounded bg-[#F2EEE6] text-neutral-700">Updated</span>
      </div>

      <div className="space-y-3">
        {items.map((a) => {
          const id = a?.id || a?._id;
          const category = String(a?.category || a?.section || "News").replace(/-/g, " ");
          const date = formatDate(a?.publishedDate || a?.published_at || a?.created_at);
          return (
            <a
              key={id}
              href={`/article/${encodeURIComponent(id)}`}
              className="block rounded-lg border border-[#E6E1D8] bg-transparent px-3 py-3 hover:bg-[#F2EEE6] transition"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] px-2 py-0.5 rounded bg-[#F2EEE6] text-neutral-700">
                  {category}
                </span>
                {date ? (
                  <span className="ml-auto flex items-center text-[11px] text-neutral-600">
                    <Clock className="h-3 w-3 mr-1" />
                    {date}
                  </span>
                ) : null}
              </div>

              <div className="text-sm font-semibold text-neutral-900 leading-snug line-clamp-2">
                {String(a?.title || "Untitled")}
              </div>
            </a>
          );
        })}
      </div>
    </section>
  );
}
