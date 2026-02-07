import React from "react";
import CompactArticleCard from "../CompactArticleCard";

export default function LatestFeed({ stories = [] }) {
  return (
    <section className="space-y-4">
      {stories.map((story) => (
        <CompactArticleCard
          key={story.id}
          article={story}
          variant="compact"
        />
      ))}
    </section>
  );
}
