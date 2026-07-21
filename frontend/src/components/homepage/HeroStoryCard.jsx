import React from "react";
import { Link } from "react-router-dom";

const formatPublishedTime = (value) => {
  if (!value) return "";

  const normalized =
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(value)
      ? `${value}Z`
      : value;

  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return String(value);

  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
};

export default function HeroStoryCard({
  image,
  category,
  town,
  headline,
  publishedTime,
  readTime,
  url,
}) {
  const [showImage, setShowImage] = React.useState(Boolean(image));
  const displayTime = formatPublishedTime(publishedTime);

  return (
    <article className="w-full border-b border-slate-200 pb-5 dark:border-gray-800">
      <Link
        to={url}
        className="group block rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A] focus-visible:ring-offset-4 dark:focus-visible:ring-offset-gray-900"
      >
        {showImage && (
          <div className="relative aspect-[21/10] w-full overflow-hidden rounded-2xl bg-slate-100 md:aspect-[4/3] dark:bg-gray-800">
            <img
              src={image}
              alt={headline}
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.025]"
              loading="eager"
              fetchPriority="high"
              decoding="sync"
              width="1200"
              height="675"
              onError={() => setShowImage(false)}
            />
            <div
              className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/35 to-transparent"
              aria-hidden="true"
            />
          </div>
        )}

        <div className={showImage ? "mt-5" : ""}>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-semibold uppercase tracking-[0.12em]">
            <span className="text-emerald-700 dark:text-emerald-400">
              {category}
            </span>
            {town && (
              <>
                <span className="text-slate-400 dark:text-gray-600" aria-hidden="true">
                  •
                </span>
                <span className="text-slate-600 dark:text-gray-300">
                  {town}
                </span>
              </>
            )}
          </div>

          <h1 className="font-headline mt-4 max-w-4xl text-[2rem] font-bold leading-[1.08] tracking-[-0.025em] text-slate-950 transition-colors group-hover:text-[#1E3A8A] sm:text-[2.35rem] lg:text-[2.75rem] dark:text-white dark:group-hover:text-blue-300">
            {headline}
          </h1>

          <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-600 dark:text-gray-300">
            {displayTime && <span>{displayTime}</span>}
            {displayTime && readTime && (
              <span className="text-slate-300 dark:text-gray-600" aria-hidden="true">
                •
              </span>
            )}
            {readTime && <span>{readTime} min read</span>}
          </div>
        </div>
      </Link>
    </article>
  );
}
