import React from "react";
import NewsHeader from "../NewsHeader";
import BreakingNewsTicker from "../BreakingNewsTicker";

export default function HomepageHeader({ breakingStories, categories, activeCategory, onCategoryChange }) {
  return (
    <>
      <NewsHeader compact categories={categories} activeCategory={activeCategory} onCategoryChange={onCategoryChange} />
      {breakingStories && breakingStories.length > 0 && (
        <BreakingNewsTicker stories={breakingStories} />
      )}
    </>
  );
}
