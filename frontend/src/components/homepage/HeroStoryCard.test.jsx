import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import HeroStoryCard from "./HeroStoryCard";

const props = {
  image: "/lead.jpg", category: "Local News", town: "Wilmslow",
  headline: "Cheshire council announces new library investment",
  publishedTime: "2026-09-28T08:00:00Z", readTime: 3,
  url: "/article/lead/library-investment",
};
let container;
let root;
beforeAll(() => { global.IS_REACT_ACT_ENVIRONMENT = true; });
beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
});
const render = (overrides = {}) => act(() => root.render(
  <MemoryRouter><HeroStoryCard {...props} {...overrides} /></MemoryRouter>
));

test("retains one link, one headline and unchanged editorial metadata", () => {
  render();
  expect(container.querySelectorAll("a")).toHaveLength(1);
  expect(container.querySelector("a").getAttribute("href")).toBe(props.url);
  expect(container.querySelectorAll("h1")).toHaveLength(1);
  expect(container.querySelector("h1").textContent).toBe(props.headline);
  for (const text of ["Local News", "Wilmslow", "28 September 2026", "3 min read"]) {
    expect(container.textContent).toContain(text);
  }
});

test("preserves image identity, crop, eager loading and high fetch priority", () => {
  render();
  const img = container.querySelector("img");
  for (const [name, value] of Object.entries({ src: props.image, alt: props.headline,
    loading: "eager", fetchpriority: "high", decoding: "sync", width: "1200", height: "675" })) {
    expect(img.getAttribute(name)).toBe(value);
  }
  expect(img.classList.contains("object-cover")).toBe(true);
  expect(img.parentElement.classList.contains("aspect-[21/10]")).toBe(true);
  expect(img.parentElement.classList.contains("md:aspect-[4/3]")).toBe(true);
});

test("uses desktop-only visual reordering without duplicate markup or changing DOM order", () => {
  render();
  const link = container.querySelector("a");
  const image = container.querySelector("img").parentElement;
  const text = container.querySelector("h1").parentElement;
  expect(link.classList.contains("lg:flex")).toBe(true);
  expect(link.classList.contains("lg:flex-col")).toBe(true);
  expect(link.children[0]).toBe(image);
  expect(link.children[1]).toBe(text);
  expect(text.classList.contains("lg:order-first")).toBe(true);
  for (const name of ["mt-5", "lg:mt-0", "lg:mb-5"]) {
    expect(text.classList.contains(name)).toBe(true);
  }
});

test("missing image retains text and does not add an image spacing gap", () => {
  render({ image: null });
  expect(container.querySelector("img")).toBeNull();
  expect(container.querySelectorAll("h1")).toHaveLength(1);
  const text = container.querySelector("h1").parentElement;
  expect(text.classList.contains("mt-5")).toBe(false);
  expect(text.classList.contains("lg:mb-5")).toBe(false);
});

test("image failure hides the image and removes image-dependent spacing", () => {
  render();
  act(() => container.querySelector("img").dispatchEvent(new Event("error")));
  expect(container.querySelector("img")).toBeNull();
  expect(container.querySelector("a").getAttribute("href")).toBe(props.url);
  expect(container.querySelectorAll("h1")).toHaveLength(1);
  expect(container.querySelector("h1").parentElement.classList.contains("lg:mb-5")).toBe(false);
});
