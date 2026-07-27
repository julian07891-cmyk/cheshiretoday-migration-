import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import NewsletterPopup from './NewsletterPopup';
import {
  NEWSLETTER_CREATED_ITEMS,
  NEWSLETTER_CREATED_SUPPORT,
  NEWSLETTER_EXISTING_MESSAGE,
  NEWSLETTER_SIGNUP_CONSENT,
} from '../constants/newsletterSignup';

const mockSubscribe = jest.fn();
jest.mock('../services/api', () => ({
  newsletterService: { subscribe: (...args) => mockSubscribe(...args) },
}));
jest.mock('@/lib/utils', () => ({
  cn: (...values) => values.filter(Boolean).join(' '),
}), { virtual: true });

let container;
let root;

beforeAll(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
});

beforeEach(() => {
  jest.useFakeTimers();
  localStorage.clear();
  mockSubscribe.mockReset();
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root.render(<MemoryRouter><NewsletterPopup /></MemoryRouter>);
  });
  act(() => {
    jest.advanceTimersByTime(15000);
  });
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  localStorage.clear();
  jest.useRealTimers();
});

const submit = async outcome => {
  mockSubscribe.mockResolvedValue({ success: true, outcome });
  const input = container.querySelector("input[type='email']");
  act(() => {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      'value',
    ).set;
    setter.call(input, 'reader@example.com');
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await act(async () => {
    container.querySelector('form').dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    );
    await Promise.resolve();
  });
};

test('popup submits its placement and confirms all three created subscriptions', async () => {
  expect(container.textContent).toContain(NEWSLETTER_SIGNUP_CONSENT);
  await submit('created');

  expect(mockSubscribe).toHaveBeenCalledWith('reader@example.com', 'popup');
  const status = container.querySelector('[role="status"][aria-live="polite"]');
  expect(status.textContent).toContain('You’re subscribed');
  NEWSLETTER_CREATED_ITEMS.forEach(item => expect(status.textContent).toContain(item));
  expect(status.textContent).toContain(NEWSLETTER_CREATED_SUPPORT);

  const close = Array.from(container.querySelectorAll('button')).find(
    button => button.textContent === 'Close',
  );
  const manage = Array.from(container.querySelectorAll('a')).find(
    link => link.textContent === 'Manage preferences',
  );
  expect(close.className).toContain('bg-emerald-600');
  expect(manage.getAttribute('href')).toBe('/newsletter/preferences');
});

test('popup existing outcome remains private and does not claim active subscription', async () => {
  await submit('existing');

  const status = container.querySelector('[role="status"][aria-live="polite"]');
  expect(status.textContent).toContain(NEWSLETTER_EXISTING_MESSAGE);
  expect(status.textContent).not.toContain('You’re subscribed');
  expect(localStorage.getItem('newsletter_subscribed')).toBeNull();
});

test('popup failures use an alert without exposing a success status', async () => {
  mockSubscribe.mockRejectedValue(new Error('offline test failure'));
  const input = container.querySelector("input[type='email']");
  act(() => {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      'value',
    ).set;
    setter.call(input, 'reader@example.com');
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await act(async () => {
    container.querySelector('form').dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    );
    await Promise.resolve();
  });

  expect(container.querySelector('[role="alert"]')).not.toBeNull();
  expect(container.querySelector('[role="status"]')).toBeNull();
});
