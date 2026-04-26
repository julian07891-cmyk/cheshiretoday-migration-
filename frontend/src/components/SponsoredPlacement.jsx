import React, { useEffect, useRef, useState } from "react";
import { getApiUrl } from "../utils/api";
import { trackEvent } from "../utils/trackEvent";

const fallbackCopy = {
  eyebrow: "Local advertising",
  title: "Reach Cheshire readers from £49/month",
  description: "Promote your business with launch-price sponsored placements across Cheshire Today.",
  cta: "View advertising options",
};

const SponsoredPlacement = ({ placement = "article_sidebar", compact = false }) => {
  const [ad, setAd] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const impressionTrackedRef = useRef(null);

  useEffect(() => {
    let mounted = true;

    async function loadPlacement() {
      try {
        const api = getApiUrl().replace(/\/$/, "");
        const res = await fetch(`${api}/api/sponsored-placements?placement=${encodeURIComponent(placement)}&limit=1`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const first = Array.isArray(data?.placements) ? data.placements[0] : null;
        if (mounted) setAd(first || null);
      } catch (_) {
        if (mounted) setAd(null);
      } finally {
        if (mounted) setLoaded(true);
      }
    }

    loadPlacement();
    return () => {
      mounted = false;
    };
  }, [placement]);

  const isPaidPlacement = Boolean(ad);
  const targetUrl = isPaidPlacement ? ad.target_url : "/advertise";
  const title = isPaidPlacement ? ad.title : fallbackCopy.title;
  const description = isPaidPlacement ? ad.description : fallbackCopy.description;
  const cta = isPaidPlacement ? (ad.cta_text || "Learn more") : fallbackCopy.cta;
  const sponsor = isPaidPlacement ? (ad.sponsor_name || "Sponsor") : fallbackCopy.eyebrow;

  useEffect(() => {
    if (!isPaidPlacement || !ad?.slug || impressionTrackedRef.current === ad.slug) return;

    impressionTrackedRef.current = ad.slug;
    const api = getApiUrl().replace(/\/$/, "");
    fetch(`${api}/api/sponsored-placements/${encodeURIComponent(ad.slug)}/impression`, {
      method: "POST"
    }).catch(() => {});
  }, [isPaidPlacement, ad?.slug]);

  if (!loaded && !compact) {
    return null;
  }

  const handleClick = () => {
    trackEvent("sponsored_placement_click", {
      placement,
      sponsored: isPaidPlacement,
      slug: ad?.slug || "advertise_cta",
      destination: targetUrl,
    });

    if (isPaidPlacement && ad?.slug) {
      const api = getApiUrl().replace(/\/$/, "");
      fetch(`${api}/api/sponsored-placements/${encodeURIComponent(ad.slug)}/click`, {
        method: "POST"
      }).catch(() => {});
    }
  };

  const inner = (
    <>
      <div className="text-[11px] font-bold uppercase tracking-wide text-amber-700 dark:text-amber-300">
        {isPaidPlacement ? "Sponsored" : fallbackCopy.eyebrow}
      </div>

      {isPaidPlacement && sponsor && (
        <div className="mt-1 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
          {sponsor}
        </div>
      )}

      {isPaidPlacement && ad.image_url && (
        <img
          src={ad.image_url}
          alt={title}
          loading="lazy"
          decoding="async"
          className="mt-3 w-full rounded-lg object-cover"
        />
      )}

      <h3 className="mt-2 text-base font-extrabold text-slate-900 dark:text-white">
        {title}
      </h3>

      {description && (
        <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          {description}
        </p>
      )}

      <span className="mt-3 inline-flex w-full items-center justify-center rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2 transition">
        {cta}
      </span>
    </>
  );

  if (isPaidPlacement) {
    return (
      <a
        href={targetUrl}
        target="_blank"
        rel="noopener noreferrer sponsored"
        onClick={handleClick}
        className="block rounded-xl border border-amber-200/80 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/20 p-4 hover:shadow-sm transition"
      >
        {inner}
      </a>
    );
  }

  return (
    <button
      type="button"
      onClick={() => {
        handleClick();
        window.location.href = targetUrl;
      }}
      className="w-full text-left rounded-xl border border-amber-200/80 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/20 p-4 hover:shadow-sm transition"
    >
      {inner}
    </button>
  );
};

export default SponsoredPlacement;
