import React from "react";

export default function HomepageLayout({ children }) {
  return (
    <main className="container mx-auto px-4 max-w-[1320px]">
      <div className="py-6 md:py-10 space-y-6">{children}</div>
    </main>
  );
}
