import React from "react";
import { Link } from "react-router-dom";

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

  return (
    <article className="w-full">
      <Link to={url} className="block group">
        {showImage && (
          <div className="relative w-full aspect-[16/9] md:aspect-[4/3] overflow-hidden rounded-xl">
            <img
              src={image}
              alt={headline}
              className="absolute inset-0 w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="eager"
              onError={() => setShowImage(false)}
            />
          </div>
        )}

        <div className={`${showImage ? "mt-4" : "mt-0"} space-y-2`}>
          <div className="text-sm text-emerald-600 font-semibold uppercase tracking-wide">
            {category} {town && `• ${town}`}
          </div>

          <h1 className="text-2xl md:text-3xl font-extrabold text-gray-900 dark:text-white leading-tight line-clamp-2">
            {headline}
          </h1>

          <div className="text-sm text-gray-500 flex items-center gap-2">
            <span>{publishedTime}</span>
            {readTime && <span>• {readTime} min read</span>}
          </div>
        </div>
      </Link>
    </article>
  );
}
