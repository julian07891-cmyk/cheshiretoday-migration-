import React from "react";
import HomepageLayout from "../components/homepage/HomepageLayout";
import HomepageHeader from "../components/homepage/HomepageHeader";
import HeroStoryCard from "../components/homepage/HeroStoryCard";
import TopStoriesGrid from "../components/homepage/TopStoriesGrid";
import LatestFeed from "../components/homepage/LatestFeed";
import NewsletterFull from "../components/homepage/NewsletterFull";

export default function HomePageV1() {
  return (
    <HomepageLayout>
      <HomepageHeader breakingStories={[]} />

      <HeroStoryCard
        image="https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1200&q=80&fit=crop"
        category="Local News"
        town="Cheshire"
        headline="Preview: Hero story headline goes here"
        publishedTime="Just now"
        readTime={3}
        url="/article-preview"
      />

      <TopStoriesGrid
        stories={[
          { id: 1, title: "Story 1" },
          { id: 2, title: "Story 2" },
          { id: 3, title: "Story 3" },
          { id: 4, title: "Story 4" },
        ]}
      />

      <LatestFeed
        stories={[
          { id: 5, title: "Latest story 1" },
          { id: 6, title: "Latest story 2" },
          { id: 7, title: "Latest story 3" },
          { id: 8, title: "Latest story 4" },
        ]}
      />

      <NewsletterFull />
    </HomepageLayout>
  );
}
