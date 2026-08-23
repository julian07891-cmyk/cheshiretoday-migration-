import React, { useEffect, useRef, useState } from "react";
import { getApiUrl } from "../utils/api";
import { trackEvent } from "../utils/trackEvent";

const fallbackCopy = {
  eyebrow: "Local advertising",
  title: "Reach Cheshire readers from £49/month",
  description: "Promote your business with launch-price sponsored placements across Cheshire Today.",
  cta: "View advertising options",
};

const SponsoredPlacement = ({
  placement = "article_sidebar",
  compact = false,
  prominent = false,
  suppressFallback = false,
  onAvailabilityChange,
}) => {
  const [ad, setAd] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const impressionTrackedRef = useRef(null);

  const getPreviewAd = () => {
    if (typeof window === "undefined") return null;

    const params = new URLSearchParams(window.location.search || "");
    if (params.get("sponsored_ad_preview") !== "1") return null;

    const forcedPlacement = params.get("sponsored_ad_placement") || "";
    if (forcedPlacement && forcedPlacement !== placement) return null;

    return {
      preview: true,
      slug: `preview-retreat-social-club-${placement}`,
      campaign_id: "preview-retreat-social-club",
      sponsor_name: params.get("sponsor_name") || "The Retreat Social Club",
      title: params.get("title") || "The Retreat Social Club Opens This July",
      description: params.get("description") || "A new inclusive social club supporting adults with learning disabilities, autism, ADHD and additional needs is opening at Hayloft Farm, Capenhurst. Join the open day on Wednesday 1 July 2026, 11am–3pm.",
      cta_text: params.get("cta_text") || "RSVP / Enquire",
      image_url: params.get("image_url") || "",
      target_url: params.get("target_url") || "mailto:theretreat@embracecare.org.uk?subject=The%20Retreat%20Social%20Club%20Open%20Day%20Enquiry",
    };
  };

  const getForcedPlacementParams = () => {
    if (typeof window === "undefined") return "";
    const params = new URLSearchParams(window.location.search || "");
    const forcedPlacement = params.get("sponsored_ad_placement") || "";
    if (forcedPlacement && forcedPlacement !== placement) return "";

    const forcedSlug = params.get("sponsored_ad_slug") || "";
    const forcedCampaign = params.get("sponsored_ad_campaign") || "";
    const query = new URLSearchParams();

    if (forcedSlug) query.set("slug", forcedSlug);
    if (forcedCampaign) query.set("campaign_id", forcedCampaign);

    const suffix = query.toString();
    return suffix ? `&${suffix}` : "";
  };

  useEffect(() => {
    let mounted = true;

    async function loadPlacement() {
      try {
        const previewAd = getPreviewAd();
        if (previewAd) {
          if (mounted) setAd(previewAd);
          return;
        }

        const api = getApiUrl().replace(/\/$/, "");
        const forceParams = getForcedPlacementParams();
        const res = await fetch(`${api}/api/sponsored-placements?placement=${encodeURIComponent(placement)}&limit=1${forceParams}`);
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
  const isHouseGuide = isPaidPlacement && (
    String(ad?.package_tier || "").toLowerCase().includes("house") ||
    String(ad?.campaign_id || "").toLowerCase().includes("ct_house")
  );
  const isAvailablePlacement = isPaidPlacement && !(suppressFallback && isHouseGuide);
  const placementLabel = isPaidPlacement ? (isHouseGuide ? "Affiliate guide" : "Sponsored") : fallbackCopy.eyebrow;
  const targetUrl = isPaidPlacement ? ad.target_url : "/advertise";
  const title = isPaidPlacement ? ad.title : fallbackCopy.title;
  const description = isPaidPlacement ? ad.description : fallbackCopy.description;
  const cta = isPaidPlacement ? (ad.cta_text || "Learn more") : fallbackCopy.cta;
  const sponsor = isPaidPlacement ? (ad.sponsor_name || "Sponsor") : fallbackCopy.eyebrow;
  const anchorKey = isPaidPlacement ? (ad.campaign_id || ad.slug || "advert") : "advertise";
  const anchorId = `sponsored-advert-${placement}-${anchorKey}`;
  const usesProminentSidebarStyle =
    compact === false && (placement === "homepage_sidebar" || prominent);
  const cardSizeClass = usesProminentSidebarStyle
    ? "p-5 lg:min-h-[300px] lg:flex lg:flex-col lg:justify-center"
    : "p-4";
  const showHomepageFallbackExtras =
    !isPaidPlacement && usesProminentSidebarStyle;

  useEffect(() => {
    if (loaded && typeof onAvailabilityChange === "function") {
      onAvailabilityChange(isAvailablePlacement);
    }
  }, [isAvailablePlacement, loaded, onAvailabilityChange]);

  useEffect(() => {
    if (!isAvailablePlacement || ad?.preview || !ad?.slug || impressionTrackedRef.current === ad.slug) return;

    impressionTrackedRef.current = ad.slug;
    const api = getApiUrl().replace(/\/$/, "");
    fetch(`${api}/api/sponsored-placements/${encodeURIComponent(ad.slug)}/impression`, {
      method: "POST"
    }).catch(() => {});
  }, [isAvailablePlacement, ad?.preview, ad?.slug]);

  if (!loaded && (!compact || suppressFallback)) {
    return null;
  }

  if (loaded && suppressFallback && (!isPaidPlacement || isHouseGuide)) {
    return null;
  }

  const handleClick = () => {
    trackEvent("sponsored_placement_click", {
      placement,
      sponsored: isPaidPlacement,
      slug: ad?.slug || "advertise_cta",
      destination: targetUrl,
    });

    if (isPaidPlacement && !ad?.preview && ad?.slug) {
      const api = getApiUrl().replace(/\/$/, "");
      fetch(`${api}/api/sponsored-placements/${encodeURIComponent(ad.slug)}/click`, {
        method: "POST"
      }).catch(() => {});
    }
  };

  const inner = (
    <>
      <div className="text-[11px] font-bold uppercase tracking-wide text-amber-700 dark:text-amber-300">
        {placementLabel}
      </div>

      {isPaidPlacement && sponsor && (
        <div className="mt-1 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
          {sponsor}
        </div>
      )}

      {isPaidPlacement && ad.image_url && (
        <a
          href={ad.image_url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Open sponsored advert image"
          className="block mt-3"
        >
          <img
            src={ad.image_url}
            alt={title}
            loading="lazy"
            decoding="async"
            className="w-full rounded-lg object-cover"
          />
        </a>
      )}

      <h3 className="mt-2 text-base font-extrabold text-slate-900 dark:text-white">
        {title}
      </h3>

      {description && (
        <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
          {description}
        </p>
      )}

      {showHomepageFallbackExtras && (
        <ul className="mt-4 space-y-2 text-sm text-slate-700 dark:text-slate-300">
          <li className="flex items-center gap-2"><span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-600" />Homepage visibility</li>
          <li className="flex items-center gap-2"><span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-600" />Local Cheshire audience</li>
          <li className="flex items-center gap-2"><span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-600" />Fast setup and approval</li>
        </ul>
      )}

      {isPaidPlacement ? (
        <a
          href={targetUrl}
          target="_blank"
          rel={isHouseGuide ? "noopener noreferrer" : "noopener noreferrer sponsored"}
          onClick={handleClick}
          className="mt-4 inline-flex w-full items-center justify-center rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2 transition"
        >
          {cta}
        </a>
      ) : (
        <span className="mt-4 inline-flex w-full items-center justify-center rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2 transition">
          {cta}
        </span>
      )}
    </>
  );

  if (isPaidPlacement) {
    return (
      <div
        id={anchorId}
        className={`block rounded-xl border border-amber-200/80 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/20 ${cardSizeClass} hover:shadow-sm transition`}
      >
        {inner}
      </div>
    );
  }

  return (
    <button
      id={anchorId}
      type="button"
      onClick={() => {
        handleClick();
        window.location.href = targetUrl;
      }}
      className={`w-full text-left rounded-xl border border-amber-200/80 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/20 ${cardSizeClass} hover:shadow-sm transition`}
    >
      {inner}
    </button>
  );
};

export default SponsoredPlacement;
