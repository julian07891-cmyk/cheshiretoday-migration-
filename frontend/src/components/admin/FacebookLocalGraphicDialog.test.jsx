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
jest.mock('../ui/button', () => ({
  Button: ({ children, variant, ...props }) => <button {...props}>{children}</button>,
}));

const ARTICLE = {
  mongo_id: '507f1f77bcf86cd799439011',
  title: 'Council investment supports new jobs in Knutsford',
  category: 'Local News',
  image: 'https://images.example.test/story.jpg',
};


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
      `https://cheshiretoday.co.uk/article/${ARTICLE.mongo_id}/council-investment-supports-new-jobs-in-knutsford`
    );
    expect(button('Generate Graphic').disabled).toBe(false);
    expect(button('Download PNG').disabled).toBe(true);
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
