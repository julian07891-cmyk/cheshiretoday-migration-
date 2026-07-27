import fs from 'fs';
import path from 'path';
import {
  NEWSLETTER_SIGNUP_CONSENT,
  buildNewsletterSignupPayload,
} from '../constants/newsletterSignup';

const read = relativePath => fs.readFileSync(
  path.join(__dirname, '..', relativePath),
  'utf8',
);

test('public payload contains only email and allow-listed placement', () => {
  expect(buildNewsletterSignupPayload('reader@example.com', 'footer')).toEqual({
    email: 'reader@example.com',
    signup_placement: 'footer',
  });
});

test('every active public signup caller uses the shared consent and placement contract', () => {
  const callers = [
    ['components/homepage/NewsletterFull.jsx', 'newsletter_landing'],
    ['components/NewsFooter.jsx', 'footer'],
    ['components/SubscribeSection.jsx', 'article'],
    ['components/NewsletterPopup.jsx', 'popup'],
  ];

  callers.forEach(([file, placement]) => {
    const source = read(file);
    expect(source).toContain('NEWSLETTER_SIGNUP_CONSENT');
    expect(source).toMatch(new RegExp(`["']${placement}["']`));
  });

  const inlineSource = read('components/JobsWidget.jsx');
  const homeSource = read('pages/HomePageV1.jsx');
  expect(inlineSource).toContain('NEWSLETTER_SIGNUP_CONSENT');
  expect(inlineSource).toContain("signupPlacement = 'article'");
  expect(homeSource).toContain('signupPlacement="homepage"');
  expect(NEWSLETTER_SIGNUP_CONSENT).toContain('rare Breaking News Alerts');
});

test('secondary signup surfaces expose accessible success and error announcements', () => {
  [
    'components/NewsFooter.jsx',
    'components/JobsWidget.jsx',
    'components/SubscribeSection.jsx',
    'components/NewsletterPopup.jsx',
  ].forEach(file => {
    const source = read(file);
    expect(source).toContain('role="status"');
    expect(source).toContain('aria-live="polite"');
    expect(source).toContain('role="alert"');
  });
});

test('shared-dialog surfaces pass through created and existing outcomes', () => {
  [
    'components/NewsFooter.jsx',
    'components/JobsWidget.jsx',
    'components/SubscribeSection.jsx',
  ].forEach(file => {
    const source = read(file);
    expect(source).toContain("response.outcome === 'created'");
    expect(source).toContain('outcome={signupOutcome}');
  });
});
