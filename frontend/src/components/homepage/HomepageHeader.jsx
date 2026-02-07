import React from "react";
import NewsHeader from "../NewsHeader";
import BreakingNewsTicker from "../BreakingNewsTicker";

export default function HomepageHeader({ breakingStories }) {
  return (
    <>
      <NewsHeader compact />
      {breakingStories && breakingStories.length > 0 && (
        <BreakingNewsTicker stories={breakingStories} />
      )}
    </>
  );
}
