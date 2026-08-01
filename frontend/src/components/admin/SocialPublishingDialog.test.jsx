import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

import SocialPublishingDialog from './SocialPublishingDialog';
import {
  FacebookSocialAssetError,
  downloadFacebookPng,
  fetchFacebookLocalGraphic,
  fetchFacebookNewsletterGraphic,
  fetchFacebookTypedGraphic,
  rasterizeFacebookSvg,
} from '../../services/facebookSocialAsset';
import {
  downloadInstagramFeedPng,
  downloadInstagramReelsCoverPng,
  downloadInstagramStoryPng,
  fetchInstagramFeed,
  fetchInstagramReelsCover,
  fetchInstagramTopStory,
  InstagramSocialAssetError,
  rasterizeInstagramFeedSvg,
  rasterizeInstagramReelsCoverSvg,
  rasterizeInstagramStorySvg,
} from '../../services/instagramSocialAsset';


jest.mock('../../services/facebookSocialAsset', () => {
  const actual = jest.requireActual('../../services/facebookSocialAsset');
  return {
    ...actual,
    downloadFacebookPng: jest.fn(),
    fetchFacebookLocalGraphic: jest.fn(),
    fetchFacebookNewsletterGraphic: jest.fn(),
    fetchFacebookTypedGraphic: jest.fn(),
    rasterizeFacebookSvg: jest.fn(),
  };
});
jest.mock('../../services/instagramSocialAsset', () => {
  const actual = jest.requireActual('../../services/instagramSocialAsset');
  return {
    ...actual,
    downloadInstagramFeedPng: jest.fn(),
    downloadInstagramReelsCoverPng: jest.fn(),
    downloadInstagramStoryPng: jest.fn(),
    fetchInstagramFeed: jest.fn(),
    fetchInstagramReelsCover: jest.fn(),
    fetchInstagramTopStory: jest.fn(),
    rasterizeInstagramFeedSvg: jest.fn(),
    rasterizeInstagramReelsCoverSvg: jest.fn(),
    rasterizeInstagramStorySvg: jest.fn(),
  };
});
jest.mock('../ui/dialog', () => ({
  Dialog: ({ open, children }) => open ? <div>{children}</div> : null,
  DialogContent: ({ children }) => <div>{children}</div>,
  DialogHeader: ({ children }) => <div>{children}</div>,
  DialogTitle: ({ children }) => <h2>{children}</h2>,
  DialogDescription: ({ children }) => <p>{children}</p>,
  DialogFooter: ({ children }) => <div>{children}</div>,
}));
jest.mock('../ui/badge', () => ({ Badge: ({ children }) => <span>{children}</span> }));
jest.mock('../ui/button', () => {
  const ReactModule = require('react');
  return {
    Button: ({ children, variant, asChild, ...props }) => asChild
      ? ReactModule.cloneElement(children, { ...props, 'data-variant': variant })
      : <button data-variant={variant} {...props}>{children}</button>,
  };
});

const ARTICLE = {
  mongo_id: '507f1f77bcf86cd799439011',
  title: 'Council investment supports new jobs in Knutsford',
  category: 'Local News',
  image: 'https://images.example.test/story.jpg',
  source_url: 'https://publisher.example.test/source-story',
  location: 'wilmslow',
};
const CANONICAL_URL = `https://cheshiretoday.co.uk/article/${ARTICLE.mongo_id}/council-investment-supports-new-jobs-in-knutsford`;
const FACEBOOK_URL = `${CANONICAL_URL}?utm_source=facebook&utm_medium=social&utm_campaign=social_publishing`;
const CAPTION = `${ARTICLE.title}\n\nRead the full story on Cheshire Today.`;
const HASHTAGS = '#CheshireToday #CheshireNews #Wilmslow #LocalNews';
const FACEBOOK_PACKAGE = `${CAPTION}\n\n${FACEBOOK_URL}\n\n${HASHTAGS}`;
const NEWSLETTER_CAPTION = "Get Cheshire’s latest local, business, property and AI & Tech stories delivered to your inbox.\n\nSign up free to the Cheshire Today newsletter.";
const NEWSLETTER_HASHTAGS = '#CheshireToday #CheshireNews #Newsletter';
const NEWSLETTER_POST = `${NEWSLETTER_CAPTION}\n\nhttps://cheshiretoday.co.uk/newsletter\n\n${NEWSLETTER_HASHTAGS}`;


describe('SocialPublishingDialog', () => {
  let container;
  let root;
  let onOpenChange;

  beforeAll(() => { global.IS_REACT_ACT_ENVIRONMENT = true; });
  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    onOpenChange = jest.fn();
    URL.createObjectURL = jest.fn(() => 'blob:svg-preview');
    URL.revokeObjectURL = jest.fn();
    fetchFacebookLocalGraphic.mockReset();
    fetchFacebookNewsletterGraphic.mockReset();
    fetchFacebookTypedGraphic.mockReset();
    rasterizeFacebookSvg.mockReset();
    downloadFacebookPng.mockReset();
    fetchInstagramTopStory.mockReset();
    fetchInstagramFeed.mockReset();
    fetchInstagramReelsCover.mockReset();
    rasterizeInstagramStorySvg.mockReset();
    rasterizeInstagramFeedSvg.mockReset();
    rasterizeInstagramReelsCoverSvg.mockReset();
    downloadInstagramStoryPng.mockReset();
    downloadInstagramFeedPng.mockReset();
    downloadInstagramReelsCoverPng.mockReset();
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: jest.fn().mockResolvedValue(undefined) },
    });
  });
  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  const renderDialog = () => act(() => root.render(
    <SocialPublishingDialog
      open
      article={ARTICLE}
      apiUrl="https://admin.example"
      token="admin-token"
      onOpenChange={onOpenChange}
    />
  ));
  const button = label => Array.from(container.querySelectorAll('button'))
    .find(node => node.textContent.includes(label));
  const click = async label => act(async () => button(label).click());
  const radio = value => container.querySelector(`input[type="radio"][value="${value}"]`);
  const selectMode = value => act(() => radio(value).click());
  const selectPlatform = value => act(() => radio(value).click());
  const changeInput = (node, value) => act(() => {
    const prototype = node.tagName === 'TEXTAREA'
      ? window.HTMLTextAreaElement.prototype
      : window.HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(prototype, 'value').set.call(node, value);
    node.dispatchEvent(new Event('input', { bubbles: true }));
  });

  test('opens in Link Preview mode with only link-preview controls', () => {
    renderDialog();
    expect(container.textContent).toContain('Social Publishing');
    expect(container.textContent).toContain(ARTICLE.title);
    expect(container.textContent).toContain('Local News');
    expect(container.querySelector('[aria-label="Canonical article URL"]').value).toBe(
      CANONICAL_URL
    );
    expect(container.querySelector('[role="radiogroup"][aria-labelledby="facebook-publishing-mode-label"]')).not.toBeNull();
    expect(radio('link-preview').checked).toBe(true);
    expect(radio('branded-graphic').checked).toBe(false);
    expect(button('Generate Graphic')).toBeUndefined();
    expect(button('Download Graphic')).toBeUndefined();
    expect(button('Copy Link').disabled).toBe(false);
    expect(button('Copy Facebook Post').dataset.variant).toBe('default');
    expect(container.querySelector('#facebook-dialog-article-actions').textContent).toBe('Article');
    expect(container.querySelector('#facebook-dialog-facebook-actions').textContent).toBe('Facebook');
    expect(container.querySelector('#facebook-dialog-graphic-actions')).toBeNull();
    expect(container.querySelector('#facebook-dialog-graphic-type-label')).toBeNull();
    const openArticle = container.querySelector('a');
    expect(openArticle.textContent).toContain('View Article');
    expect(openArticle.href).toBe(
      CANONICAL_URL
    );
    expect(openArticle.target).toBe('_blank');
    expect(openArticle.rel).toBe('noopener noreferrer');
  });

  test('Branded Graphic mode exposes only its article, Facebook and graphic controls', () => {
    renderDialog();
    selectMode('branded-graphic');
    expect(radio('branded-graphic').checked).toBe(true);
    expect(container.querySelector('a').textContent).toContain('View Article');
    expect(button('Copy Caption')).toBeDefined();
    expect(button('Copy Hashtags')).toBeDefined();
    expect(button('Generate Graphic')).toBeDefined();
    expect(button('Download Graphic')).toBeDefined();
    expect(button('Copy Link')).toBeUndefined();
    expect(button('Copy Facebook Post')).toBeUndefined();
    expect(container.querySelector('#facebook-dialog-graphic-actions').textContent).toBe('Graphics');
    expect(container.querySelector('#facebook-dialog-graphic-type-label').textContent).toBe('Graphic Type');
    expect(radio('local-news').checked).toBe(true);
    expect(radio('newsletter').checked).toBe(false);
  });

  test('Branded Graphic mode exposes all nine allow-listed graphic types', () => {
    renderDialog();
    selectMode('branded-graphic');
    expect(Array.from(container.querySelectorAll('input[name="facebook-graphic-type"]')).map(node => node.value)).toEqual([
      'local-news', 'newsletter', 'business', 'property', 'ai-tech',
      'breaking-news', 'event', 'quote', 'poll',
    ]);
    expect(radio('local-news').checked).toBe(true);
  });

  test.each(['business', 'property', 'ai-tech', 'event'])(
    '%s calls only the narrow approved typed endpoint',
    async graphicType => {
      fetchFacebookTypedGraphic.mockResolvedValue(new Blob(['<svg/>'], { type: 'image/svg+xml' }));
      renderDialog();
      selectMode('branded-graphic');
      selectMode(graphicType);
      expect(fetchFacebookTypedGraphic).not.toHaveBeenCalled();
      await click('Generate Graphic');
      expect(fetchFacebookTypedGraphic).toHaveBeenCalledWith({
        apiUrl: 'https://admin.example', graphicType, mongoId: ARTICLE.mongo_id,
        token: 'admin-token', payload: undefined,
      });
      expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
      expect(fetchFacebookNewsletterGraphic).not.toHaveBeenCalled();
    }
  );

  test('Breaking News cannot generate without explicit editor confirmation', async () => {
    fetchFacebookTypedGraphic.mockResolvedValue(new Blob(['<svg/>'], { type: 'image/svg+xml' }));
    renderDialog();
    selectMode('branded-graphic');
    selectMode('breaking-news');
    expect(button('Generate Graphic').disabled).toBe(true);
    const confirmation = container.querySelector('input[type="checkbox"]');
    act(() => confirmation.click());
    expect(button('Generate Graphic').disabled).toBe(false);
    await click('Generate Graphic');
    expect(fetchFacebookTypedGraphic).toHaveBeenCalledWith(expect.objectContaining({ graphicType: 'breaking-news' }));
  });

  test('Quote requires verified text and sends only the approved payload', async () => {
    fetchFacebookTypedGraphic.mockResolvedValue(new Blob(['<svg/>'], { type: 'image/svg+xml' }));
    renderDialog();
    selectMode('branded-graphic');
    selectMode('quote');
    expect(container.textContent).toContain('Use only a verified quotation');
    expect(button('Generate Graphic').disabled).toBe(true);
    const quote = container.querySelector('[aria-label="Verified quote"]');
    const attribution = container.querySelector('[aria-label="Quote attribution"]');
    expect(quote.maxLength).toBe(240);
    expect(attribution.maxLength).toBe(80);
    expect(container.textContent).toContain('Quote maximum 240 characters; attribution maximum 80 characters.');
    changeInput(quote, 'Investment will support Cheshire jobs');
    changeInput(attribution, 'Jane Smith');
    await click('Generate Graphic');
    expect(fetchFacebookTypedGraphic).toHaveBeenCalledWith(expect.objectContaining({
      graphicType: 'quote',
      payload: { quote: 'Investment will support Cheshire jobs', attribution: 'Jane Smith' },
    }));
  });

  test('Poll requires exactly two options and provides non-interactive guidance', async () => {
    fetchFacebookTypedGraphic.mockResolvedValue(new Blob(['<svg/>'], { type: 'image/svg+xml' }));
    renderDialog();
    selectMode('branded-graphic');
    selectMode('poll');
    expect(container.textContent).toContain('reply in comments');
    expect(button('Generate Graphic').disabled).toBe(true);
    const values = [
      ['Poll question', 'Should Cheshire invest more?'],
      ['Poll option A', 'Yes'],
      ['Poll option B', 'No'],
    ];
    values.forEach(([label, value]) => {
      const input = container.querySelector(`[aria-label="${label}"]`);
      changeInput(input, value);
    });
    expect(container.querySelector('[aria-label="Poll question"]').maxLength).toBe(140);
    expect(container.querySelector('[aria-label="Poll option A"]').maxLength).toBe(48);
    expect(container.querySelector('[aria-label="Poll option B"]').maxLength).toBe(48);
    expect(container.textContent).toContain('Question maximum 140 characters; each option maximum 48 characters.');
    await click('Generate Graphic');
    expect(fetchFacebookTypedGraphic).toHaveBeenCalledWith(expect.objectContaining({
      graphicType: 'poll',
      payload: { question: 'Should Cheshire invest more?', option_a: 'Yes', option_b: 'No' },
    }));
  });

  test.each([
    ['business', 'cheshire-today-business-facebook.png'],
    ['property', 'cheshire-today-property-facebook.png'],
    ['ai-tech', 'cheshire-today-ai-tech-facebook.png'],
    ['event', 'cheshire-today-event-facebook.png'],
  ])('%s downloads with its exact deterministic filename', async (graphicType, filename) => {
    const svgBlob = new Blob(['<svg/>'], { type: 'image/svg+xml' });
    const pngBlob = new Blob(['png'], { type: 'image/png' });
    fetchFacebookTypedGraphic.mockResolvedValue(svgBlob);
    rasterizeFacebookSvg.mockResolvedValue(pngBlob);
    renderDialog();
    selectMode('branded-graphic');
    selectMode(graphicType);
    await click('Generate Graphic');
    await click('Download Graphic');
    expect(downloadFacebookPng).toHaveBeenCalledWith({ pngBlob, filename });
  });

  test.each([
    ['breaking-news', 'cheshire-today-breaking-news-facebook.png'],
    ['quote', 'cheshire-today-quote-facebook.png'],
    ['poll', 'cheshire-today-poll-facebook.png'],
  ])('%s downloads with its exact deterministic filename', async (graphicType, filename) => {
    const svgBlob = new Blob(['<svg/>'], { type: 'image/svg+xml' });
    const pngBlob = new Blob(['png'], { type: 'image/png' });
    fetchFacebookTypedGraphic.mockResolvedValue(svgBlob);
    rasterizeFacebookSvg.mockResolvedValue(pngBlob);
    renderDialog();
    selectMode('branded-graphic');
    selectMode(graphicType);
    if (graphicType === 'breaking-news') {
      act(() => container.querySelector('input[type="checkbox"]').click());
    } else if (graphicType === 'quote') {
      changeInput(container.querySelector('[aria-label="Verified quote"]'), 'Verified quote');
      changeInput(container.querySelector('[aria-label="Quote attribution"]'), 'Named source');
    } else {
      changeInput(container.querySelector('[aria-label="Poll question"]'), 'Your view?');
      changeInput(container.querySelector('[aria-label="Poll option A"]'), 'Yes');
      changeInput(container.querySelector('[aria-label="Poll option B"]'), 'No');
    }
    await click('Generate Graphic');
    await click('Download Graphic');
    expect(downloadFacebookPng).toHaveBeenCalledWith({ pngBlob, filename });
  });

  test('Newsletter type hides article publishing controls and exposes deterministic Newsletter copy', async () => {
    renderDialog();
    selectMode('branded-graphic');
    selectMode('newsletter');
    expect(radio('newsletter').checked).toBe(true);
    expect(container.querySelector('#facebook-dialog-article-actions')).toBeNull();
    expect(container.querySelector('a')).toBeNull();
    expect(button('Copy Link')).toBeUndefined();
    expect(button('Copy Facebook Post')).toBeUndefined();
    expect(button('Copy Newsletter Post')).toBeDefined();

    await click('Copy Newsletter Post');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(NEWSLETTER_POST);
    expect(NEWSLETTER_POST).not.toContain(CANONICAL_URL);
    expect(NEWSLETTER_POST).not.toContain(ARTICLE.source_url);
    expect(NEWSLETTER_POST).not.toContain(ARTICLE.image);
    expect(container.querySelector('[role="status"][aria-live="polite"]').textContent).toBe('Newsletter post copied');

    await click('Copy Caption');
    expect(navigator.clipboard.writeText).toHaveBeenLastCalledWith(NEWSLETTER_CAPTION);
    await click('Copy Hashtags');
    expect(navigator.clipboard.writeText).toHaveBeenLastCalledWith(NEWSLETTER_HASHTAGS);
  });

  test('switching modes preserves existing clipboard status without triggering work', async () => {
    renderDialog();
    await click('Copy Caption');
    expect(container.textContent).toContain('Caption copied');
    selectMode('branded-graphic');
    expect(container.textContent).toContain('Caption copied');
    selectMode('link-preview');
    expect(container.textContent).toContain('Caption copied');
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test('copies only the deterministic Facebook campaign URL and keeps View Article canonical', async () => {
    renderDialog();
    await click('Copy Link');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      FACEBOOK_URL
    );
    const viewArticle = Array.from(container.querySelectorAll('a')).find(link => link.textContent.includes('View Article'));
    expect(viewArticle.getAttribute('href')).toBe(CANONICAL_URL);
    expect(navigator.clipboard.writeText).not.toHaveBeenCalledWith(ARTICLE.image);
    expect(navigator.clipboard.writeText).not.toHaveBeenCalledWith(ARTICLE.source_url);
    const status = container.querySelector('[role="status"][aria-live="polite"]');
    expect(status.textContent).toBe('Link copied');
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test.each([
    ['Copy Caption', CAPTION, 'Caption copied'],
    ['Copy Hashtags', HASHTAGS, 'Hashtags copied'],
    ['Copy Facebook Post', FACEBOOK_PACKAGE, 'Facebook post copied'],
  ])('%s copies deterministic text and announces success', async (label, expected, confirmation) => {
    renderDialog();
    await click(label);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expected);
    expect(expected).not.toContain(ARTICLE.source_url);
    expect(expected).not.toContain(ARTICLE.image);
    expect(expected).not.toContain('https://admin.example');
    const status = container.querySelector('[role="status"][aria-live="polite"]');
    expect(status.textContent).toBe(confirmation);
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test.each([
    ['Copy Caption', 'The Facebook caption could not be copied. Please copy it manually.'],
    ['Copy Hashtags', 'The hashtags could not be copied. Please copy them manually.'],
    ['Copy Facebook Post', 'The Facebook package could not be copied. Please copy it manually.'],
  ])('%s shows its safe failure message', async (label, expected) => {
    navigator.clipboard.writeText.mockRejectedValue(new Error('private detail'));
    renderDialog();
    await click(label);
    expect(container.querySelector('[role="alert"]').textContent).toBe(expected);
    expect(container.textContent).not.toContain('private detail');
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test('shows a safe copy error without triggering graphic work', async () => {
    navigator.clipboard.writeText.mockRejectedValue(new Error('private detail'));
    renderDialog();
    await click('Copy Link');
    expect(container.querySelector('[role="alert"]').textContent).toBe(
      'The article link could not be copied. Please copy it manually.'
    );
    expect(container.textContent).not.toContain('private detail');
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
  });

  test('clears copy confirmation when the selected article changes or dialog closes', async () => {
    renderDialog();
    await click('Copy Caption');
    expect(container.textContent).toContain('Caption copied');

    const replacement = { ...ARTICLE, mongo_id: '507f191e810c19729de860ea', title: 'Replacement article' };
    act(() => root.render(
      <SocialPublishingDialog
        open
        article={replacement}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(container.textContent).not.toContain('Caption copied');

    await click('Copy Caption');
    expect(container.textContent).toContain('Caption copied');
    await click('Close');
    expect(container.textContent).not.toContain('Caption copied');
  });

  test('does not restore copy confirmation after closing during a pending clipboard request', async () => {
    let resolveCopy;
    navigator.clipboard.writeText.mockReturnValue(new Promise(resolve => { resolveCopy = resolve; }));
    renderDialog();
    act(() => button('Copy Facebook Post').click());
    await click('Close');
    await act(async () => resolveCopy());
    expect(container.textContent).not.toContain('Facebook post copied');
  });

  test('disables canonical-link actions when the Mongo ID is unavailable', () => {
    act(() => root.render(
      <SocialPublishingDialog
        open
        article={{ ...ARTICLE, mongo_id: '' }}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(button('Copy Link').disabled).toBe(true);
    expect(button('View Article').disabled).toBe(true);
    expect(button('Copy Facebook Post').disabled).toBe(true);
    expect(container.querySelector('a')).toBeNull();
  });

  test('disables caption and package without a title and hashtags without an article', () => {
    act(() => root.render(
      <SocialPublishingDialog
        open
        article={{ ...ARTICLE, title: '' }}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(button('Copy Caption').disabled).toBe(true);
    expect(button('Copy Facebook Post').disabled).toBe(true);

    act(() => root.render(
      <SocialPublishingDialog
        open
        article={null}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(button('Copy Hashtags').disabled).toBe(true);
  });

  test('shows loading then enables SVG preview and graphic download', async () => {
    let resolveFetch;
    fetchFacebookLocalGraphic.mockReturnValue(new Promise(resolve => { resolveFetch = resolve; }));
    renderDialog();
    selectMode('branded-graphic');
    act(() => button('Generate Graphic').click());
    expect(button('Generating…').disabled).toBe(true);
    expect(container.querySelector('[role="status"][aria-live="polite"]')).not.toBeNull();
    expect(fetchFacebookLocalGraphic).toHaveBeenCalledWith({
      apiUrl: 'https://admin.example',
      mongoId: ARTICLE.mongo_id,
      token: 'admin-token',
    });
    const svgBlob = new Blob(['<svg/>'], { type: 'image/svg+xml' });
    await act(async () => resolveFetch(svgBlob));
    expect(URL.createObjectURL).toHaveBeenCalledWith(svgBlob);
    expect(container.querySelector('[alt="Generated Facebook Local News graphic preview"]').src).toContain('blob:svg-preview');
    expect(button('Download Graphic').disabled).toBe(false);
    expect(container.querySelector('[role="status"][aria-live="polite"]').textContent).toBe('Graphic generated');
    expect(button('Regenerate').dataset.variant).toBe('outline');
  });

  test('retains a generated preview across mode switches without extra work', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    renderDialog();
    selectMode('branded-graphic');
    await click('Generate Graphic');
    expect(container.querySelector('[alt="Generated Facebook Local News graphic preview"]')).not.toBeNull();

    selectMode('link-preview');
    expect(container.querySelector('[alt="Generated Facebook Local News graphic preview"]')).toBeNull();
    expect(button('Generate Graphic')).toBeUndefined();
    selectMode('branded-graphic');
    expect(container.querySelector('[alt="Generated Facebook Local News graphic preview"]').src).toContain('blob:svg-preview');
    expect(button('Regenerate')).toBeDefined();
    expect(fetchFacebookLocalGraphic).toHaveBeenCalledTimes(1);
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test('restores Link Preview mode when the dialog closes or article changes', () => {
    renderDialog();
    selectMode('branded-graphic');
    expect(radio('branded-graphic').checked).toBe(true);
    act(() => button('Close').click());
    expect(radio('link-preview').checked).toBe(true);

    selectMode('branded-graphic');
    act(() => root.render(
      <SocialPublishingDialog
        open
        article={{ ...ARTICLE, mongo_id: '507f191e810c19729de860ea' }}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(radio('link-preview').checked).toBe(true);
  });

  test('restores Local News graphic type when the dialog closes or article changes', () => {
    renderDialog();
    selectMode('branded-graphic');
    selectMode('newsletter');
    act(() => button('Close').click());
    selectMode('branded-graphic');
    expect(radio('local-news').checked).toBe(true);

    selectMode('newsletter');
    act(() => root.render(
      <SocialPublishingDialog
        open
        article={{ ...ARTICLE, mongo_id: '507f191e810c19729de860ea' }}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    selectMode('branded-graphic');
    expect(radio('local-news').checked).toBe(true);
  });

  test('switching graphic type clears and revokes only the previous preview', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    renderDialog();
    selectMode('branded-graphic');
    await click('Generate Graphic');
    expect(container.textContent).toContain('Graphic generated');
    selectMode('newsletter');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:svg-preview');
    expect(container.querySelector('[alt*="graphic preview"]')).toBeNull();
    expect(container.textContent).not.toContain('Graphic generated');
    expect(fetchFacebookLocalGraphic).toHaveBeenCalledTimes(1);
    expect(fetchFacebookNewsletterGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test('type changes clear copy status and suppress stale clipboard completion', async () => {
    renderDialog();
    selectMode('branded-graphic');
    await click('Copy Caption');
    expect(container.textContent).toContain('Caption copied');
    selectMode('newsletter');
    expect(container.textContent).not.toContain('Caption copied');

    let resolveCopy;
    navigator.clipboard.writeText.mockReturnValue(new Promise(resolve => { resolveCopy = resolve; }));
    act(() => button('Copy Newsletter Post').click());
    selectMode('local-news');
    await act(async () => resolveCopy());
    expect(container.textContent).not.toContain('Newsletter post copied');
  });

  test('downloads the rasterised preview with the article title contract', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    const pngBlob = new Blob(['png'], { type: 'image/png' });
    rasterizeFacebookSvg.mockResolvedValue(pngBlob);
    renderDialog();
    selectMode('branded-graphic');
    await click('Generate Graphic');
    await click('Download Graphic');
    expect(rasterizeFacebookSvg).toHaveBeenCalledWith({ svgUrl: 'blob:svg-preview' });
    expect(downloadFacebookPng).toHaveBeenCalledWith({ pngBlob, title: ARTICLE.title });
    expect(container.querySelector('[role="status"][aria-live="polite"]').textContent).toBe('Graphic downloaded');
  });

  test('generates and downloads Newsletter graphic through its narrow contract', async () => {
    fetchFacebookNewsletterGraphic.mockResolvedValue(new Blob(['newsletter-svg'], { type: 'image/svg+xml' }));
    rasterizeFacebookSvg.mockResolvedValue(new Blob(['png'], { type: 'image/png' }));
    renderDialog();
    selectMode('branded-graphic');
    selectMode('newsletter');
    await click('Generate Graphic');
    expect(fetchFacebookNewsletterGraphic).toHaveBeenCalledWith({
      apiUrl: 'https://admin.example',
      token: 'admin-token',
    });
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(container.querySelector('[alt="Generated Facebook Newsletter graphic preview"]')).not.toBeNull();
    await click('Download Graphic');
    const pngBlob = await rasterizeFacebookSvg.mock.results[0].value;
    expect(downloadFacebookPng).toHaveBeenCalledWith({
      pngBlob,
      filename: 'cheshire-today-newsletter-facebook.png',
    });
    expect(container.textContent).toContain('Graphic downloaded');
  });

  test.each([
    [404, 'This article is no longer available.'],
    [400, 'This article is not supported by the Local News template.'],
    [422, 'This article does not have a usable featured image.'],
    [500, 'The Facebook graphic could not be generated. Please try again.'],
  ])('shows a safe error for %s', async (status, expected) => {
    fetchFacebookLocalGraphic.mockRejectedValue(new FacebookSocialAssetError(status));
    renderDialog();
    selectMode('branded-graphic');
    await click('Generate Graphic');
    expect(container.textContent).toContain(expected);
  });

  test('revokes preview object URLs on regenerate, close and unmount', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    URL.createObjectURL
      .mockReturnValueOnce('blob:first')
      .mockReturnValueOnce('blob:second');
    renderDialog();
    selectMode('branded-graphic');
    await click('Generate Graphic');
    await click('Regenerate');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:first');
    await click('Close');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:second');
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  test('revokes an active preview when the dialog component unmounts', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    URL.createObjectURL.mockReturnValue('blob:unmount-preview');
    renderDialog();
    selectMode('branded-graphic');
    await click('Generate Graphic');
    act(() => root.unmount());
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:unmount-preview');
    root = createRoot(container);
  });

  test('does not download a stale rasterisation after the dialog closes', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    let resolveRaster;
    rasterizeFacebookSvg.mockReturnValue(new Promise(resolve => { resolveRaster = resolve; }));
    renderDialog();
    selectMode('branded-graphic');
    await click('Generate Graphic');
    act(() => button('Download Graphic').click());
    expect(container.textContent).toContain('Creating PNG…');
    await click('Close');
    await act(async () => resolveRaster(new Blob(['png'], { type: 'image/png' })));
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test('defaults to Facebook and exposes the exact approved Instagram formats', () => {
    renderDialog();
    expect(radio('facebook').checked).toBe(true);
    expect(radio('instagram').checked).toBe(false);
    selectPlatform('instagram');
    expect(radio('instagram').checked).toBe(true);
    expect(radio('story').checked).toBe(true);
    expect(radio('feed')).not.toBeNull();
    expect(radio('reels-cover')).not.toBeNull();
    expect(radio('top-story').checked).toBe(true);
    expect(button('Generate Story Preview')).toBeDefined();
    expect(button('Download Story PNG')).toBeDefined();
    expect(button('Copy Facebook Post')).toBeUndefined();
    expect(button('Copy Story Package')).toBeDefined();
    expect(button('Copy Story Caption')).toBeDefined();
    expect(button('Copy Story Hashtags')).toBeDefined();
    expect(radio('link-preview')).toBeNull();
    expect(fetchInstagramTopStory).not.toHaveBeenCalled();
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
  });

  test('generates previews and downloads exact Instagram Story output', async () => {
    const svgBlob = new Blob(['story-svg'], { type: 'image/svg+xml' });
    const pngBlob = new Blob(['story-png'], { type: 'image/png' });
    fetchInstagramTopStory.mockResolvedValue(svgBlob);
    rasterizeInstagramStorySvg.mockResolvedValue(pngBlob);
    renderDialog();
    selectPlatform('instagram');
    await click('Generate Story Preview');
    expect(fetchInstagramTopStory).toHaveBeenCalledWith({
      apiUrl: 'https://admin.example',
      mongoId: ARTICLE.mongo_id,
      token: 'admin-token',
    });
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(container.querySelector('[alt="Generated Instagram Story Top Story preview"]')).not.toBeNull();
    expect(container.textContent).toContain('Preview generated');
    await click('Download Story PNG');
    expect(rasterizeInstagramStorySvg).toHaveBeenCalledWith({ svgUrl: 'blob:svg-preview' });
    expect(downloadInstagramStoryPng).toHaveBeenCalledWith({ pngBlob, title: ARTICLE.title });
    expect(container.textContent).toContain('PNG downloaded');
  });

  test('switching platform clears and revokes the Instagram preview without generating', async () => {
    fetchInstagramTopStory.mockResolvedValue(new Blob(['story-svg'], { type: 'image/svg+xml' }));
    URL.createObjectURL.mockReturnValue('blob:instagram-preview');
    renderDialog();
    selectPlatform('instagram');
    await click('Generate Story Preview');
    selectPlatform('facebook');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:instagram-preview');
    expect(container.querySelector('[alt="Generated Instagram Story Top Story preview"]')).toBeNull();
    expect(fetchInstagramTopStory).toHaveBeenCalledTimes(1);
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
  });

  test('stale Instagram results and safe errors cannot escape the active platform', async () => {
    let resolveStory;
    fetchInstagramTopStory.mockReturnValue(new Promise(resolve => { resolveStory = resolve; }));
    renderDialog();
    selectPlatform('instagram');
    act(() => button('Generate Story Preview').click());
    selectPlatform('facebook');
    await act(async () => resolveStory(new Blob(['late-story'], { type: 'image/svg+xml' })));
    expect(URL.createObjectURL).not.toHaveBeenCalled();
    expect(container.querySelector('[alt="Generated Instagram Story Top Story preview"]')).toBeNull();

    selectPlatform('instagram');
    fetchInstagramTopStory.mockRejectedValue(new InstagramSocialAssetError(422));
    await click('Generate Story Preview');
    expect(container.textContent).toContain('This article does not have a usable featured image.');
  });

  test.each([
    ['feed', 'Feed', fetchInstagramFeed, rasterizeInstagramFeedSvg, downloadInstagramFeedPng, 'Generated Instagram Feed Local News preview'],
    ['reels-cover', 'Reels Cover', fetchInstagramReelsCover, rasterizeInstagramReelsCoverSvg, downloadInstagramReelsCoverPng, 'Generated Instagram Reels Cover Local News preview'],
  ])('generates, previews and downloads Instagram %s without automatic requests', async (
    format, label, fetcher, rasterizer, downloader, altText
  ) => {
    const svgBlob = new Blob([`${format}-svg`], { type: 'image/svg+xml' });
    const pngBlob = new Blob([`${format}-png`], { type: 'image/png' });
    fetcher.mockResolvedValue(svgBlob);
    rasterizer.mockResolvedValue(pngBlob);
    renderDialog();
    selectPlatform('instagram');
    selectMode(format);
    expect(fetcher).not.toHaveBeenCalled();
    expect(radio('local-news').checked).toBe(true);
    await click(`Generate ${label} Preview`);
    expect(fetcher).toHaveBeenCalledWith({
      apiUrl: 'https://admin.example',
      mongoId: ARTICLE.mongo_id,
      token: 'admin-token',
    });
    expect(container.querySelector(`[alt="${altText}"]`)).not.toBeNull();
    await click(`Download ${label} PNG`);
    expect(rasterizer).toHaveBeenCalledWith({ svgUrl: 'blob:svg-preview' });
    expect(downloader).toHaveBeenCalledWith({ pngBlob, title: ARTICLE.title });
    expect(button(label === 'Feed' ? 'Copy Instagram Post' : 'Copy Reel Post')).toBeDefined();
    expect(button(label === 'Feed' ? 'Copy Caption' : 'Copy Reel Caption')).toBeDefined();
    expect(button('Copy Hashtags')).toBeDefined();
  });

  test('format switching revokes preview, makes no request and blocks stale cross-format results', async () => {
    let resolveStory;
    fetchInstagramTopStory.mockReturnValue(new Promise(resolve => { resolveStory = resolve; }));
    renderDialog();
    selectPlatform('instagram');
    act(() => button('Generate Story Preview').click());
    selectMode('feed');
    expect(fetchInstagramFeed).not.toHaveBeenCalled();
    await act(async () => resolveStory(new Blob(['late-story'], { type: 'image/svg+xml' })));
    expect(URL.createObjectURL).not.toHaveBeenCalled();

    fetchInstagramFeed.mockResolvedValue(new Blob(['feed'], { type: 'image/svg+xml' }));
    await click('Generate Feed Preview');
    expect(container.querySelector('[alt="Generated Instagram Feed Local News preview"]')).not.toBeNull();
    selectMode('reels-cover');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:svg-preview');
    expect(container.querySelector('[alt="Generated Instagram Feed Local News preview"]')).toBeNull();
    expect(fetchInstagramReelsCover).not.toHaveBeenCalled();
  });

  test.each([
    [
      'story',
      'Copy Story Caption',
      `${ARTICLE.title}\n\nTap the link sticker to read the full story on Cheshire Today.`,
      'Story caption copied',
    ],
    [
      'feed',
      'Copy Caption',
      `${ARTICLE.title}\n\nRead the full story on Cheshire Today.`,
      'Caption copied',
    ],
    [
      'reels-cover',
      'Copy Reel Caption',
      `${ARTICLE.title}\n\nFind the full story on Cheshire Today.`,
      'Reel caption copied',
    ],
  ])('copies exact %s caption without generation or network work', async (
    format, label, expected, successMessage
  ) => {
    renderDialog();
    selectPlatform('instagram');
    if (format !== 'story') selectMode(format);
    await click(label);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expected);
    expect(container.textContent).toContain(successMessage);
    expect(container.querySelector('[role="status"]').textContent).toContain(successMessage);
    expect(fetchInstagramTopStory).not.toHaveBeenCalled();
    expect(fetchInstagramFeed).not.toHaveBeenCalled();
    expect(fetchInstagramReelsCover).not.toHaveBeenCalled();
    expect(rasterizeInstagramStorySvg).not.toHaveBeenCalled();
    expect(rasterizeInstagramFeedSvg).not.toHaveBeenCalled();
    expect(rasterizeInstagramReelsCoverSvg).not.toHaveBeenCalled();
  });

  test('copies the Story package with editor-only canonical link-sticker guidance', async () => {
    renderDialog();
    selectPlatform('instagram');
    await click('Copy Story Package');
    const copied = navigator.clipboard.writeText.mock.calls[0][0];
    expect(copied).toBe(
      `${ARTICLE.title}\n\nTap the link sticker to read the full story on Cheshire Today.\n\nLink sticker (editor use): ${CANONICAL_URL}\n\n${HASHTAGS}`
    );
    expect(copied).not.toContain(ARTICLE.source_url);
    expect(copied).not.toContain(ARTICLE.image);
    expect(copied).not.toContain('/admin/');
  });

  test.each([
    ['feed', 'Copy Instagram Post', `${ARTICLE.title}\n\nRead the full story on Cheshire Today.\n\n${HASHTAGS}`],
    ['reels-cover', 'Copy Reel Post', `${ARTICLE.title}\n\nFind the full story on Cheshire Today.\n\n${HASHTAGS}`],
  ])('%s public package contains no raw URL or clickable-link claim', async (format, label, expected) => {
    renderDialog();
    selectPlatform('instagram');
    selectMode(format);
    await click(label);
    const copied = navigator.clipboard.writeText.mock.calls[0][0];
    expect(copied).toBe(expected);
    expect(copied).not.toMatch(/https?:\/\/|clickable|link in bio/i);
    expect(copied).not.toContain(ARTICLE.source_url);
    expect(copied).not.toContain(ARTICLE.image);
  });

  test('Instagram hashtags use stored locality and never source or image data', async () => {
    renderDialog();
    selectPlatform('instagram');
    await click('Copy Story Hashtags');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(HASHTAGS);
    expect(navigator.clipboard.writeText.mock.calls[0][0].split(' ')).toHaveLength(4);
  });

  test.each(['story', 'feed', 'reels-cover'])('Instagram %s copies only the canonical article link without other work', async format => {
    renderDialog();
    selectPlatform('instagram');
    if (format !== 'story') selectMode(format);
    await click('Copy Link');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(CANONICAL_URL);
    expect(container.textContent).toContain('Link copied');
    expect(navigator.clipboard.writeText.mock.calls[0][0]).not.toContain(ARTICLE.source_url);
    expect(navigator.clipboard.writeText.mock.calls[0][0]).not.toContain(ARTICLE.image);
    expect(navigator.clipboard.writeText.mock.calls[0][0]).not.toContain('/admin/');
    expect(fetchInstagramTopStory).not.toHaveBeenCalled();
    expect(fetchInstagramFeed).not.toHaveBeenCalled();
    expect(fetchInstagramReelsCover).not.toHaveBeenCalled();
    expect(rasterizeInstagramStorySvg).not.toHaveBeenCalled();
    expect(rasterizeInstagramFeedSvg).not.toHaveBeenCalled();
    expect(rasterizeInstagramReelsCoverSvg).not.toHaveBeenCalled();
    expect(downloadInstagramStoryPng).not.toHaveBeenCalled();
    expect(downloadInstagramFeedPng).not.toHaveBeenCalled();
    expect(downloadInstagramReelsCoverPng).not.toHaveBeenCalled();
  });

  test('Instagram Copy Link uses safe failure feedback and blocks stale completion', async () => {
    navigator.clipboard.writeText.mockRejectedValueOnce(new Error('private clipboard detail'));
    renderDialog();
    selectPlatform('instagram');
    await click('Copy Link');
    expect(container.textContent).toContain('The article link could not be copied. Please copy it manually.');
    expect(container.textContent).not.toContain('private clipboard detail');

    let resolveCopy;
    navigator.clipboard.writeText.mockReturnValue(new Promise(resolve => { resolveCopy = resolve; }));
    act(() => button('Copy Link').click());
    selectMode('feed');
    await act(async () => resolveCopy());
    expect(container.textContent).not.toContain('Link copied');
  });

  test('Instagram copy failure is safe and format switching clears feedback', async () => {
    navigator.clipboard.writeText.mockRejectedValue(new Error('private clipboard detail'));
    renderDialog();
    selectPlatform('instagram');
    await click('Copy Story Caption');
    expect(container.textContent).toContain(
      'The Instagram Story caption could not be copied. Please copy it manually.'
    );
    expect(container.textContent).not.toContain('private clipboard detail');
    selectMode('feed');
    expect(container.textContent).not.toContain('could not be copied');
  });

  test('stale Instagram clipboard completion cannot restore status after format or platform switch', async () => {
    let resolveCopy;
    navigator.clipboard.writeText.mockReturnValue(new Promise(resolve => { resolveCopy = resolve; }));
    renderDialog();
    selectPlatform('instagram');
    act(() => button('Copy Story Caption').click());
    selectMode('feed');
    await act(async () => resolveCopy());
    expect(container.textContent).not.toContain('Story caption copied');

    navigator.clipboard.writeText.mockResolvedValue(undefined);
    await click('Copy Caption');
    expect(container.textContent).toContain('Caption copied');
    selectPlatform('facebook');
    expect(container.textContent).not.toContain('Caption copied');
  });

  test('Threads exposes ready-to-paste native copy and requires editorial approval', () => {
    renderDialog();
    selectPlatform('threads');
    expect(radio('threads').checked).toBe(true);
    expect(container.textContent).toContain('Threads editorial approval');
    expect(container.textContent).toContain('40% Local');
    expect(container.querySelector('[aria-label="Verified opening line"]')).toBeNull();
    expect(container.querySelector('[aria-label="Verified context"]')).toBeNull();
    expect(container.querySelector('pre').textContent.trim()).toBe(
      `${ARTICLE.title}\n\nRead the full story on Cheshire Today.\n\n${CANONICAL_URL}`
    );
    expect(button('Copy Threads Post').disabled).toBe(true);
    expect(button('Generate Graphic')).toBeUndefined();
    expect(button('Generate Story Preview')).toBeUndefined();
    expect(button('Download PNG')).toBeUndefined();
    expect(button('Copy Facebook Post')).toBeUndefined();
    expect(button('Copy Instagram Post')).toBeUndefined();
  });

  test('constructs, previews and copies the exact ready-to-paste Threads post', async () => {
    const expected = `${ARTICLE.title}\n\nRead the full story on Cheshire Today.\n\n${CANONICAL_URL}`;
    renderDialog();
    selectPlatform('threads');
    expect(container.querySelector('pre').textContent.trim()).toBe(expected);
    expect(button('Copy Threads Post').disabled).toBe(true);
    act(() => container.querySelector('input[type="checkbox"]').click());
    expect(button('Copy Threads Post').disabled).toBe(false);
    await click('Copy Threads Post');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expected);
    expect(container.textContent).toContain('Threads post copied');
    expect(container.querySelector('[role="status"]').textContent).toContain('Threads post copied');
    expect(expected).not.toContain('#');
    expect(expected).not.toContain(ARTICLE.source_url);
    expect(expected).not.toContain(ARTICLE.image);
    expect(fetchInstagramTopStory).not.toHaveBeenCalled();
    expect(fetchInstagramFeed).not.toHaveBeenCalled();
    expect(fetchInstagramReelsCover).not.toHaveBeenCalled();
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test('Threads approval and copy state reset on platform switch and close', async () => {
    renderDialog();
    selectPlatform('threads');
    act(() => container.querySelector('input[type="checkbox"]').click());
    expect(button('Copy Threads Post').disabled).toBe(false);
    selectPlatform('facebook');
    selectPlatform('threads');
    expect(container.querySelector('input[type="checkbox"]').checked).toBe(false);
    await click('Close');
    expect(radio('facebook').checked).toBe(true);
    selectPlatform('threads');
    expect(container.querySelector('input[type="checkbox"]').checked).toBe(false);
  });

  test('article change clears Threads approval and copy feedback', async () => {
    renderDialog();
    selectPlatform('threads');
    act(() => container.querySelector('input[type="checkbox"]').click());
    await click('Copy Threads Post');
    expect(container.textContent).toContain('Threads post copied');
    await act(async () => root.render(
      <SocialPublishingDialog
        open
        article={{ ...ARTICLE, mongo_id: '607f1f77bcf86cd799439011', title: 'Another approved article' }}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(radio('facebook').checked).toBe(true);
    expect(container.textContent).not.toContain('Threads post copied');
  });

  test('Threads clipboard failure is safe and stale completion cannot restore status after close', async () => {
    renderDialog();
    selectPlatform('threads');
    act(() => container.querySelector('input[type="checkbox"]').click());
    navigator.clipboard.writeText.mockRejectedValueOnce(new Error('private clipboard detail'));
    await click('Copy Threads Post');
    expect(container.textContent).toContain('The Threads post could not be copied. Please copy it manually.');
    expect(container.textContent).not.toContain('private clipboard detail');

    let resolveCopy;
    navigator.clipboard.writeText.mockReturnValue(new Promise(resolve => { resolveCopy = resolve; }));
    act(() => button('Copy Threads Post').click());
    await click('Close');
    await act(async () => resolveCopy());
    expect(container.textContent).not.toContain('Threads post copied');
  });
});
