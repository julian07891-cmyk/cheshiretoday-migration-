import React from "react";
import CompactArticleCard from "../CompactArticleCard";

export default function TopStoriesGrid({ stories = [] }) {
  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 gap-6">
      {stories.slice(0, 4).map((story) => (
        <CompactArticleCard
          key={story.id}
          article={story}
          variant="standard"
        />
      ))}
    </section>
  );
}
