import React, { act } from "react";
import { createRoot } from "react-dom/client";
import fs from "fs";
import path from "path";
import CompactArticleCard from "./CompactArticleCard";

const summary = "The council confirmed " + "additional verified details ".repeat(10) + "in its report.";

test.each(["", "/image.jpg"])("complete summary survives card rendering, image=%s", (image) => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const container = document.createElement("div");
  const root = createRoot(container);
  const onClick = jest.fn();
  const article = { id: "test", title: "Verified report", summary, content: "Different body.", image };
  try {
    act(() => root.render(<CompactArticleCard article={article} onClick={onClick} />));
    const paragraph = container.querySelector("p");
    expect(paragraph.textContent).toBe(summary);
    expect(paragraph.className).toMatch(/line-clamp-[23]/);
    act(() => container.firstChild.dispatchEvent(new MouseEvent("click", { bubbles: true })));
    expect(onClick).toHaveBeenCalledWith(article);
    expect(onClick).toHaveBeenCalledTimes(1);
  } finally { act(() => root.unmount()); }
});

test("visible article intro preserves the complete stored summary, including short summaries", () => {
  const source = fs.readFileSync(path.join(__dirname, "../pages/ArticlePageV2.jsx"), "utf8");
  const fn = source.slice(source.indexOf("function buildVisibleIntro("), source.indexOf("function slugifyArticleTitle("));
  const intro = new Function("safeText", `${fn}; return buildVisibleIntro;`)((value) => String(value || ""));
  expect(intro({ summary })).toBe(summary);
  expect(intro({ summary: "Work starts tomorrow." })).toBe("Work starts tomorrow.");
  expect(intro({ summary: "", content: "An unfinished body" })).toBe("");
});

test.each([
  ["", ""], ["", null], ["", undefined],
  ["/image.jpg", ""], ["/image.jpg", null], ["/image.jpg", undefined],
])("card does not fall back to body: image=%s summary=%s", (image, storedSummary) => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  const container = document.createElement("div");
  const root = createRoot(container);
  const article = { id: "test", title: "Verified report", image, content: "Full article body must not become a preview." };
  if (storedSummary !== undefined) article.summary = storedSummary;
  try {
    act(() => root.render(<CompactArticleCard article={article} onClick={jest.fn()} />));
    expect(container.querySelector("p").textContent).toBe("");
    expect(container.querySelector("p").className).toMatch(/line-clamp-[23]/);
    expect(container.textContent).not.toContain(article.content);
  } finally { act(() => root.unmount()); }
});
