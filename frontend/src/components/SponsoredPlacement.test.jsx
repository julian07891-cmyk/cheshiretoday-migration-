import React, { act } from "react";
import { createRoot } from "react-dom/client";

import SponsoredPlacement from "./SponsoredPlacement";

jest.mock("../utils/api", () => ({ getApiUrl: () => "https://example.test" }));
jest.mock("../utils/trackEvent", () => ({ trackEvent: jest.fn() }));

let container;
let root;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  jest.restoreAllMocks();
});

const renderPlacement = async (props = {}, placements = []) => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ placements }),
  });

  await act(async () => {
    root.render(<SponsoredPlacement {...props} />);
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
};

test("article placements can suppress the house fallback without changing availability semantics", async () => {
  const onAvailabilityChange = jest.fn();
  await renderPlacement(
    {
      placement: "article_sidebar",
      suppressFallback: true,
      onAvailabilityChange,
    },
    []
  );

  expect(container.textContent).toBe("");
  expect(onAvailabilityChange).toHaveBeenLastCalledWith(false);
});

test("compact article placement does not flash the house fallback while loading", async () => {
  global.fetch = jest.fn(() => new Promise(() => {}));

  await act(async () => {
    root.render(
      <SponsoredPlacement
        placement="article_mobile"
        compact
        suppressFallback
      />
    );
  });

  expect(container.textContent).toBe("");
});

test("the existing homepage house fallback remains the default", async () => {
  await renderPlacement({ placement: "homepage_sidebar" }, []);

  expect(container.textContent).toContain("Reach Cheshire readers from £49/month");
  expect(container.textContent).toContain("View advertising options");
});

test("genuine sponsor inventory still renders and reports availability", async () => {
  const onAvailabilityChange = jest.fn();
  await renderPlacement(
    {
      placement: "article_sidebar",
      suppressFallback: true,
      onAvailabilityChange,
    },
    [{
      slug: "local-sponsor",
      campaign_id: "paid-local-campaign",
      sponsor_name: "Cheshire Business",
      title: "Local sponsor message",
      description: "A genuine paid placement.",
      cta_text: "Learn more",
      target_url: "https://sponsor.example/",
    }]
  );

  expect(container.textContent).toContain("Sponsored");
  expect(container.textContent).toContain("Local sponsor message");
  expect(onAvailabilityChange).toHaveBeenLastCalledWith(true);
});
