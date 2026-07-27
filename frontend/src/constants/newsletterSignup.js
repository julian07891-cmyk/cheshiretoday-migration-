export const NEWSLETTER_SIGNUP_CONSENT =
  "By subscribing, you agree to receive The Daily Brief from Monday to Saturday, The Weekly Roundup on Sunday, and rare Breaking News Alerts for major incidents. You can unsubscribe or change your preferences at any time.";

export const NEWSLETTER_SIGNUP_OUTCOMES = {
  CREATED: "created",
  EXISTING: "existing",
};

export const NEWSLETTER_CREATED_TITLE = "You’re subscribed";
export const NEWSLETTER_CREATED_LEAD = "You’ll receive:";
export const NEWSLETTER_CREATED_ITEMS = [
  "The Daily Brief, Monday to Saturday",
  "The Weekly Roundup on Sunday",
  "Rare Breaking News Alerts for major incidents",
];
export const NEWSLETTER_CREATED_SUPPORT =
  "You can unsubscribe or change your preferences securely at any time.";
export const NEWSLETTER_EXISTING_MESSAGE =
  "Thanks. If this address is eligible, no further action is needed.";

export const buildNewsletterSignupPayload = (email, signupPlacement) => ({
  email,
  signup_placement: signupPlacement,
});
