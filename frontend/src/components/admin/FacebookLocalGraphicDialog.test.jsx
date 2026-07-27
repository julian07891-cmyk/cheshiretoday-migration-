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
  const radio = value => container.querySelector(`input[type="radio"][value="${value}"]`);
  const selectMode = value => act(() => radio(value).click());

  test('opens in Link Preview mode with only link-preview controls', () => {
    renderDialog();
    expect(container.textContent).toContain('Facebook Graphic');
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

  test('copies only the canonical Cheshire Today article URL and announces success', async () => {
    renderDialog();
    await click('Copy Link');
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
      <FacebookLocalGraphicDialog
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
      <FacebookLocalGraphicDialog
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
      <FacebookLocalGraphicDialog
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
    expect(container.querySelector('[alt="Generated Facebook graphic preview"]').src).toContain('blob:svg-preview');
    expect(button('Download Graphic').disabled).toBe(false);
    expect(container.querySelector('[role="status"][aria-live="polite"]').textContent).toBe('Graphic generated');
    expect(button('Regenerate').dataset.variant).toBe('outline');
  });

  test('retains a generated preview across mode switches without extra work', async () => {
    fetchFacebookLocalGraphic.mockResolvedValue(new Blob(['svg'], { type: 'image/svg+xml' }));
    renderDialog();
    selectMode('branded-graphic');
    await click('Generate Graphic');
    expect(container.querySelector('[alt="Generated Facebook graphic preview"]')).not.toBeNull();

    selectMode('link-preview');
    expect(container.querySelector('[alt="Generated Facebook graphic preview"]')).toBeNull();
    expect(button('Generate Graphic')).toBeUndefined();
    selectMode('branded-graphic');
    expect(container.querySelector('[alt="Generated Facebook graphic preview"]').src).toContain('blob:svg-preview');
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
      <FacebookLocalGraphicDialog
        open
        article={{ ...ARTICLE, mongo_id: '507f191e810c19729de860ea' }}
        apiUrl="https://admin.example"
        token="admin-token"
        onOpenChange={onOpenChange}
      />
    ));
    expect(radio('link-preview').checked).toBe(true);
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
});
