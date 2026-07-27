import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Copy, Download, ExternalLink, Image as ImageIcon, Loader2, RefreshCw } from 'lucide-react';

import { buildArticleUrl } from '../../utils/articleUrl';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import {
  FacebookSocialAssetError,
  downloadFacebookPng,
  fetchFacebookLocalGraphic,
  rasterizeFacebookSvg,
} from '../../services/facebookSocialAsset';
import {
  buildFacebookCaption,
  buildFacebookHashtags,
  buildFacebookPackage,
} from '../../services/facebookPublishingCopy';


const errorMessage = (error) => {
  if (error instanceof FacebookSocialAssetError) {
    if (error.status === 404) return 'This article is no longer available.';
    if (error.status === 400) return 'This article is not supported by the Local News template.';
    if (error.status === 422) return 'This article does not have a usable featured image.';
  }
  return 'The Facebook graphic could not be generated. Please try again.';
};


const FacebookLocalGraphicDialog = ({ open, article, apiUrl, token, onOpenChange }) => {
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [copyError, setCopyError] = useState('');
  const [previewUrl, setPreviewUrl] = useState(null);
  const previewUrlRef = useRef(null);
  const requestSequence = useRef(0);
  const copySequence = useRef(0);

  const revokePreview = useCallback((clearState = true) => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
    if (clearState) setPreviewUrl(null);
  }, []);

  const reset = useCallback(() => {
    requestSequence.current += 1;
    copySequence.current += 1;
    revokePreview();
    setLoading(false);
    setDownloading(false);
    setError('');
    setStatusMessage('');
    setCopyError('');
  }, [revokePreview]);

  useEffect(() => {
    reset();
  }, [open, article?.mongo_id, reset]);

  useEffect(() => () => {
    requestSequence.current += 1;
    copySequence.current += 1;
    revokePreview(false);
  }, [revokePreview]);

  const handleOpenChange = (nextOpen) => {
    if (!nextOpen) reset();
    onOpenChange(nextOpen);
  };

  const generate = async () => {
    const sequence = requestSequence.current + 1;
    requestSequence.current = sequence;
    revokePreview();
    setError('');
    setStatusMessage('');
    setLoading(true);
    try {
      const svgBlob = await fetchFacebookLocalGraphic({
        apiUrl,
        mongoId: article?.mongo_id,
        token,
      });
      if (requestSequence.current !== sequence) return;
      const objectUrl = URL.createObjectURL(svgBlob);
      previewUrlRef.current = objectUrl;
      setPreviewUrl(objectUrl);
      setStatusMessage('Graphic generated');
    } catch (requestError) {
      if (requestSequence.current === sequence) setError(errorMessage(requestError));
    } finally {
      if (requestSequence.current === sequence) setLoading(false);
    }
  };

  const download = async () => {
    if (!previewUrl) return;
    const sequence = requestSequence.current;
    setError('');
    setStatusMessage('');
    setDownloading(true);
    try {
      const pngBlob = await rasterizeFacebookSvg({ svgUrl: previewUrl });
      if (requestSequence.current !== sequence) return;
      downloadFacebookPng({ pngBlob, title: article?.title });
      setStatusMessage('Graphic downloaded');
    } catch (_error) {
      if (requestSequence.current === sequence) {
        setError('The PNG could not be created. Please try again.');
      }
    } finally {
      if (requestSequence.current === sequence) setDownloading(false);
    }
  };

  const canonicalUrl = article?.mongo_id
    ? `https://cheshiretoday.co.uk${buildArticleUrl({ ...article, id: article.mongo_id })}`
    : '';

  const caption = buildFacebookCaption(article?.title);
  const hashtags = buildFacebookHashtags(article);
  const facebookPackage = buildFacebookPackage({ article, canonicalUrl });

  const copyText = async ({ text, successMessage, failureMessage }) => {
    if (!text) return;
    const sequence = copySequence.current + 1;
    copySequence.current = sequence;
    setStatusMessage('');
    setCopyError('');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(text);
      if (copySequence.current === sequence) setStatusMessage(successMessage);
    } catch (_error) {
      if (copySequence.current === sequence) {
        setCopyError(failureMessage);
      }
    }
  };

  const copyArticleLink = () => copyText({
    text: canonicalUrl,
    successMessage: 'Link copied',
    failureMessage: 'The article link could not be copied. Please copy it manually.',
  });

  const copyFacebookCaption = () => copyText({
    text: caption,
    successMessage: 'Caption copied',
    failureMessage: 'The Facebook caption could not be copied. Please copy it manually.',
  });

  const copyHashtags = () => copyText({
    text: hashtags,
    successMessage: 'Hashtags copied',
    failureMessage: 'The hashtags could not be copied. Please copy them manually.',
  });

  const copyFacebookPackage = () => copyText({
    text: facebookPackage,
    successMessage: 'Facebook post copied',
    failureMessage: 'The Facebook package could not be copied. Please copy it manually.',
  });

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ImageIcon className="h-5 w-5 text-blue-700" />
            Facebook Graphic
          </DialogTitle>
          <DialogDescription>
            Generate a preview and download it without changing or publishing the article.
          </DialogDescription>
        </DialogHeader>

        {article && (
          <div className="space-y-5">
            <section aria-label="Selected article" className="rounded-lg border bg-gray-50 p-4 dark:bg-gray-900">
              <div className="flex items-start gap-4">
                <img src={article.image} alt="" className="h-20 w-20 flex-shrink-0 rounded-md object-cover" />
                <div className="min-w-0 space-y-2">
                  <h3 className="font-semibold text-gray-950 dark:text-white">{article.title}</h3>
                  <Badge variant="secondary">{article.category}</Badge>
                  <input
                    aria-label="Canonical article URL"
                    readOnly
                    value={canonicalUrl}
                    className="w-full rounded border bg-white px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300"
                  />
                </div>
              </div>
            </section>

            {error && <div role="alert" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
            {copyError && <div role="alert" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{copyError}</div>}
            {statusMessage && <div role="status" aria-live="polite" className="text-sm font-medium text-emerald-700">{statusMessage}</div>}

            {previewUrl && (
              <section aria-label="Generated SVG preview">
                <img
                  src={previewUrl}
                  alt="Generated Facebook graphic preview"
                  className="w-full rounded-lg border bg-white"
                />
              </section>
            )}
          </div>
        )}

        <DialogFooter className="block space-y-3">
          <section aria-labelledby="facebook-dialog-article-actions">
            <h3 id="facebook-dialog-article-actions" className="mb-2 text-sm font-semibold">Article</h3>
            <div className="flex flex-wrap gap-2">
              {canonicalUrl ? (
                <Button variant="outline" asChild>
                  <a href={canonicalUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-2 h-4 w-4" />View Article
                  </a>
                </Button>
              ) : (
                <Button type="button" variant="outline" disabled>
                  <ExternalLink className="mr-2 h-4 w-4" />View Article
                </Button>
              )}
              <Button type="button" variant="outline" onClick={copyArticleLink} disabled={!canonicalUrl}>
                <Copy className="mr-2 h-4 w-4" />Copy Link
              </Button>
            </div>
          </section>
          <section aria-labelledby="facebook-dialog-facebook-actions">
            <h3 id="facebook-dialog-facebook-actions" className="mb-2 text-sm font-semibold">Facebook</h3>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant={previewUrl ? 'default' : 'outline'} onClick={copyFacebookPackage} disabled={!facebookPackage}>
                <Copy className="mr-2 h-4 w-4" />Copy Facebook Post
              </Button>
              <Button type="button" variant="outline" onClick={copyFacebookCaption} disabled={!caption}>
                <Copy className="mr-2 h-4 w-4" />Copy Caption
              </Button>
              <Button type="button" variant="outline" onClick={copyHashtags} disabled={!hashtags}>
                <Copy className="mr-2 h-4 w-4" />Copy Hashtags
              </Button>
            </div>
          </section>
          <section aria-labelledby="facebook-dialog-graphic-actions">
            <h3 id="facebook-dialog-graphic-actions" className="mb-2 text-sm font-semibold">Graphics</h3>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant={previewUrl ? 'outline' : 'default'} onClick={generate} disabled={loading || downloading || !article?.mongo_id}>
                {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /><span role="status" aria-live="polite">Generating…</span></> : previewUrl ? <><RefreshCw className="mr-2 h-4 w-4" />Regenerate</> : <><ImageIcon className="mr-2 h-4 w-4" />Generate Graphic</>}
              </Button>
              <Button type="button" variant="outline" onClick={download} disabled={!previewUrl || loading || downloading}>
                {downloading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /><span role="status" aria-live="polite">Creating PNG…</span></> : <><Download className="mr-2 h-4 w-4" />Download Graphic</>}
              </Button>
            </div>
          </section>
          <div className="flex justify-end">
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>Close</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};


export default FacebookLocalGraphicDialog;
