import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

import FacebookLocalGraphicDialog from './FacebookLocalGraphicDialog';
import {
  FacebookSocialAssetError,
  downloadFacebookPng,
  fetchFacebookLocalGraphic,
  rasterizeFacebookSvg,
} from '../../services/facebookSocialAsset';


jest.mock('../../services/facebookSocialAsset', () => {
  const actual = jest.requireActual('../../services/facebookSocialAsset');
  return {
    ...actual,
    downloadFacebookPng: jest.fn(),
    fetchFacebookLocalGraphic: jest.fn(),
    rasterizeFacebookSvg: jest.fn(),
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
      ? ReactModule.cloneElement(children, props)
      : <button {...props}>{children}</button>,
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
const CAPTION = `${ARTICLE.title}\n\nRead the full story on Cheshire Today.`;
const HASHTAGS = '#CheshireToday #CheshireNews #Wilmslow #LocalNews';
const FACEBOOK_PACKAGE = `${CAPTION}\n\n${CANONICAL_URL}\n\n${HASHTAGS}`;


describe('FacebookLocalGraphicDialog', () => {
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
    rasterizeFacebookSvg.mockReset();
    downloadFacebookPng.mockReset();
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
    <FacebookLocalGraphicDialog
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

  test('opens with the selected article, canonical URL and Generate button', () => {
    renderDialog();
    expect(container.textContent).toContain('Facebook Graphic');
    expect(container.textContent).toContain(ARTICLE.title);
    expect(container.textContent).toContain('Local News');
    expect(container.querySelector('[aria-label="Canonical article URL"]').value).toBe(
      CANONICAL_URL
    );
    expect(button('Generate Graphic').disabled).toBe(false);
    expect(button('Download PNG').disabled).toBe(true);
    expect(button('Copy Article Link').disabled).toBe(false);
    const openArticle = container.querySelector('a');
    expect(openArticle.textContent).toContain('Open Article');
    expect(openArticle.href).toBe(
      CANONICAL_URL
    );
    expect(openArticle.target).toBe('_blank');
    expect(openArticle.rel).toBe('noopener noreferrer');
  });

  test('copies only the canonical Cheshire Today article URL and announces success', async () => {
    renderDialog();
    await click('Copy Article Link');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      CANONICAL_URL
    );
    expect(navigator.clipboard.writeText).not.toHaveBeenCalledWith(ARTICLE.image);
    expect(navigator.clipboard.writeText).not.toHaveBeenCalledWith(ARTICLE.source_url);
    const status = container.querySelector('[role="status"][aria-live="polite"]');
    expect(status.textContent).toBe('Link copied');
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });

  test.each([
    ['Copy Facebook Caption', CAPTION, 'Caption copied'],
    ['Copy Hashtags', HASHTAGS, 'Hashtags copied'],
    ['Copy Facebook Package', FACEBOOK_PACKAGE, 'Facebook package copied'],
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
    ['Copy Facebook Caption', 'The Facebook caption could not be copied. Please copy it manually.'],
    ['Copy Hashtags', 'The hashtags could not be copied. Please copy them manually.'],
    ['Copy Facebook Package', 'The Facebook package could not be copied. Please copy it manually.'],
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
    await click('Copy Article Link');
    expect(container.querySelector('[role="alert"]').textContent).toBe(
      'The article link could not be copied. Please copy it manually.'
    );
    expect(container.textContent).not.toContain('private detail');
    expect(fetchFacebookLocalGraphic).not.toHaveBeenCalled();
    expect(rasterizeFacebookSvg).not.toHaveBeenCalled();
  });

  test('clears copy confirmation when the selected article changes or dialog closes', async () => {
    renderDialog();
    await click('Copy Facebook Caption');
    expect(container.textContent).toContain('Caption copied');

    const replacement = { ...ARTICLE, mongo_id: '507f191e810c19729de860ea', title: 'Replacement article' };
    act(() => root.render(
      <FacebookLocalGraphicDialog
        open
        article={replacement}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(container.textContent).not.toContain('Caption copied');

    await click('Copy Facebook Caption');
    expect(container.textContent).toContain('Caption copied');
    await click('Close');
    expect(container.textContent).not.toContain('Caption copied');
  });

  test('does not restore copy confirmation after closing during a pending clipboard request', async () => {
    let resolveCopy;
    navigator.clipboard.writeText.mockReturnValue(new Promise(resolve => { resolveCopy = resolve; }));
    renderDialog();
    act(() => button('Copy Facebook Package').click());
    await click('Close');
    await act(async () => resolveCopy());
    expect(container.textContent).not.toContain('Facebook package copied');
  });

  test('disables canonical-link actions when the Mongo ID is unavailable', () => {
    act(() => root.render(
      <FacebookLocalGraphicDialog
        open
        article={{ ...ARTICLE, mongo_id: '' }}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(button('Copy Article Link').disabled).toBe(true);
    expect(button('Open Article').disabled).toBe(true);
    expect(button('Copy Facebook Package').disabled).toBe(true);
    expect(container.querySelector('a')).toBeNull();
  });

  test('disables caption and package without a title and hashtags without an article', () => {
    act(() => root.render(
      <FacebookLocalGraphicDialog
        open
        article={{ ...ARTICLE, title: '' }}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(button('Copy Facebook Caption').disabled).toBe(true);
    expect(button('Copy Facebook Package').disabled).toBe(true);

    act(() => root.render(
      <FacebookLocalGraphicDialog
        open
        article={null}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(button('Copy Hashtags').disabled).toBe(true);
  });

  test('shows loading then enables SVG preview and PNG download', async () => {
    let resolveFetch;
    fetchFacebookLocalGraphic.mockReturnValue(new Promise(resolve => { resolveFetch = resolve; }));
    renderDialog();
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
    expect(container.querySelector('[alt="Generated Facebook graphic preview"]').src).toContain('blob:svg-preview');
    expect(button('Download PNG').disabled).toBe(false);
  });

  test('downloads the rasterised preview with the article title contract', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    const pngBlob = new Blob(['png'], { type: 'image/png' });
    rasterizeFacebookSvg.mockResolvedValue(pngBlob);
    renderDialog();
    await click('Generate Graphic');
    await click('Download PNG');
    expect(rasterizeFacebookSvg).toHaveBeenCalledWith({ svgUrl: 'blob:svg-preview' });
    expect(downloadFacebookPng).toHaveBeenCalledWith({ pngBlob, title: ARTICLE.title });
  });

  test.each([
    [404, 'This article is no longer available.'],
    [400, 'This article is not supported by the Local News template.'],
    [422, 'This article does not have a usable featured image.'],
    [500, 'The Facebook graphic could not be generated. Please try again.'],
  ])('shows a safe error for %s', async (status, expected) => {
    fetchFacebookLocalGraphic.mockRejectedValue(new FacebookSocialAssetError(status));
    renderDialog();
    await click('Generate Graphic');
    expect(container.textContent).toContain(expected);
  });

  test('revokes preview object URLs on regenerate, close and unmount', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    URL.createObjectURL
      .mockReturnValueOnce('blob:first')
      .mockReturnValueOnce('blob:second');
    renderDialog();
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
    await click('Generate Graphic');
    act(() => button('Download PNG').click());
    expect(container.textContent).toContain('Creating PNG…');
    await click('Close');
    await act(async () => resolveRaster(new Blob(['png'], { type: 'image/png' })));
    expect(downloadFacebookPng).not.toHaveBeenCalled();
  });
});
