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
  fetchFacebookNewsletterGraphic,
  fetchFacebookTypedGraphic,
  rasterizeFacebookSvg,
} from '../../services/facebookSocialAsset';
import {
  buildFacebookCaption,
  buildFacebookHashtags,
  buildFacebookPackage,
  buildNewsletterFacebookPost,
  buildGraphicTypeCaption,
  buildGraphicTypeHashtags,
  NEWSLETTER_CAPTION,
  NEWSLETTER_HASHTAGS,
} from '../../services/facebookPublishingCopy';


const GRAPHIC_TYPES = Object.freeze([
  { value: 'local-news', label: 'Local News', filename: null },
  { value: 'newsletter', label: 'Newsletter', filename: 'cheshire-today-newsletter-facebook.png' },
  { value: 'business', label: 'Business', filename: 'cheshire-today-business-facebook.png' },
  { value: 'property', label: 'Property', filename: 'cheshire-today-property-facebook.png' },
  { value: 'ai-tech', label: 'AI & Tech', filename: 'cheshire-today-ai-tech-facebook.png' },
  { value: 'breaking-news', label: 'Breaking News', filename: 'cheshire-today-breaking-news-facebook.png' },
  { value: 'event', label: 'Event', filename: 'cheshire-today-event-facebook.png' },
  { value: 'quote', label: 'Quote', filename: 'cheshire-today-quote-facebook.png' },
  { value: 'poll', label: 'Poll', filename: 'cheshire-today-poll-facebook.png' },
]);


const errorMessage = (error, graphicType) => {
  if (error instanceof FacebookSocialAssetError) {
    if (error.status === 404) return 'This article is no longer available.';
    if (error.status === 400) return graphicType === 'local-news'
      ? 'This article is not supported by the Local News template.'
      : 'This article or editor input is not supported by the selected graphic type.';
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
  const [publishingMode, setPublishingMode] = useState('link-preview');
  const [graphicType, setGraphicType] = useState('local-news');
  const [breakingConfirmed, setBreakingConfirmed] = useState(false);
  const [quoteText, setQuoteText] = useState('');
  const [quoteAttribution, setQuoteAttribution] = useState('');
  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptionA, setPollOptionA] = useState('');
  const [pollOptionB, setPollOptionB] = useState('');
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
    setPublishingMode('link-preview');
    setGraphicType('local-news');
    setBreakingConfirmed(false);
    setQuoteText('');
    setQuoteAttribution('');
    setPollQuestion('');
    setPollOptionA('');
    setPollOptionB('');
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

  const changeGraphicType = (nextType) => {
    if (nextType === graphicType) return;
    requestSequence.current += 1;
    copySequence.current += 1;
    revokePreview();
    setLoading(false);
    setDownloading(false);
    setError('');
    setStatusMessage('');
    setCopyError('');
    setGraphicType(nextType);
    setBreakingConfirmed(false);
  };

  const generate = async () => {
    const sequence = requestSequence.current + 1;
    requestSequence.current = sequence;
    revokePreview();
    setError('');
    setStatusMessage('');
    setLoading(true);
    try {
      let svgBlob;
      if (graphicType === 'newsletter') {
        svgBlob = await fetchFacebookNewsletterGraphic({ apiUrl, token });
      } else if (graphicType === 'local-news') {
        svgBlob = await fetchFacebookLocalGraphic({
          apiUrl,
          mongoId: article?.mongo_id,
          token,
        });
      } else {
        svgBlob = await fetchFacebookTypedGraphic({
          apiUrl,
          graphicType,
          mongoId: article?.mongo_id,
          token,
          payload: graphicType === 'quote'
            ? { quote: quoteText, attribution: quoteAttribution }
            : graphicType === 'poll'
              ? { question: pollQuestion, option_a: pollOptionA, option_b: pollOptionB }
              : undefined,
        });
      }
      if (requestSequence.current !== sequence) return;
      const objectUrl = URL.createObjectURL(svgBlob);
      previewUrlRef.current = objectUrl;
      setPreviewUrl(objectUrl);
      setStatusMessage('Graphic generated');
    } catch (requestError) {
      if (requestSequence.current === sequence) setError(errorMessage(requestError, graphicType));
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
      const explicitFilename = GRAPHIC_TYPES.find(type => type.value === graphicType)?.filename;
      if (explicitFilename) {
        downloadFacebookPng({
          pngBlob,
          filename: explicitFilename,
        });
      } else {
        downloadFacebookPng({ pngBlob, title: article?.title });
      }
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
  const newsletterPost = buildNewsletterFacebookPost();
  const typedCaption = buildGraphicTypeCaption({
    graphicType, article, quote: quoteText, attribution: quoteAttribution,
    question: pollQuestion, optionA: pollOptionA, optionB: pollOptionB,
  });
  const typedHashtags = buildGraphicTypeHashtags({ graphicType, article });
  const activeCaption = graphicType === 'newsletter'
    ? NEWSLETTER_CAPTION
    : graphicType === 'local-news' ? caption : typedCaption;
  const activeHashtags = graphicType === 'newsletter'
    ? NEWSLETTER_HASHTAGS
    : graphicType === 'local-news' ? hashtags : typedHashtags;
  const editorFieldsValid = graphicType === 'quote'
    ? quoteText.trim() && quoteText.length <= 240 && quoteAttribution.trim() && quoteAttribution.length <= 80
    : graphicType === 'poll'
      ? pollQuestion.trim() && pollQuestion.length <= 140
        && pollOptionA.trim() && pollOptionA.length <= 48
        && pollOptionB.trim() && pollOptionB.length <= 48
      : true;
  const canGenerate = Boolean(
    (graphicType === 'newsletter' || article?.mongo_id)
    && editorFieldsValid
    && (graphicType !== 'breaking-news' || breakingConfirmed)
  );

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
    text: activeCaption,
    successMessage: 'Caption copied',
    failureMessage: 'The Facebook caption could not be copied. Please copy it manually.',
  });

  const copyHashtags = () => copyText({
    text: activeHashtags,
    successMessage: 'Hashtags copied',
    failureMessage: 'The hashtags could not be copied. Please copy them manually.',
  });

  const copyFacebookPackage = () => copyText({
    text: facebookPackage,
    successMessage: 'Facebook post copied',
    failureMessage: 'The Facebook package could not be copied. Please copy it manually.',
  });

  const copyNewsletterPost = () => copyText({
    text: newsletterPost,
    successMessage: 'Newsletter post copied',
    failureMessage: 'The Newsletter post could not be copied. Please copy it manually.',
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

        <div role="radiogroup" aria-labelledby="facebook-publishing-mode-label" className="space-y-2">
          <p id="facebook-publishing-mode-label" className="text-sm font-semibold">Publishing Mode</p>
          <div className="flex flex-wrap gap-2">
            <label className="flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
              <input
                type="radio"
                name="facebook-publishing-mode"
                value="link-preview"
                checked={publishingMode === 'link-preview'}
                onChange={() => setPublishingMode('link-preview')}
              />
              <span>Link Preview <span className="text-muted-foreground">(Recommended)</span></span>
            </label>
            <label className="flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
              <input
                type="radio"
                name="facebook-publishing-mode"
                value="branded-graphic"
                checked={publishingMode === 'branded-graphic'}
                onChange={() => setPublishingMode('branded-graphic')}
              />
              <span>Branded Graphic</span>
            </label>
          </div>
        </div>

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

            {publishingMode === 'branded-graphic' && previewUrl && (
              <section aria-label="Generated SVG preview">
                <img
                  src={previewUrl}
                  alt={`Generated Facebook ${GRAPHIC_TYPES.find(type => type.value === graphicType)?.label || ''} graphic preview`}
                  className="w-full rounded-lg border bg-white"
                />
              </section>
            )}
          </div>
        )}

        <DialogFooter className="block space-y-3">
          {(publishingMode === 'link-preview' || graphicType !== 'newsletter') && (
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
                {publishingMode === 'link-preview' && (
                  <Button type="button" variant="outline" onClick={copyArticleLink} disabled={!canonicalUrl}>
                    <Copy className="mr-2 h-4 w-4" />Copy Link
                  </Button>
                )}
              </div>
            </section>
          )}
          <section aria-labelledby="facebook-dialog-facebook-actions">
            <h3 id="facebook-dialog-facebook-actions" className="mb-2 text-sm font-semibold">Facebook</h3>
            <div className="flex flex-wrap gap-2">
              {publishingMode === 'link-preview' && (
                <Button type="button" variant="default" onClick={copyFacebookPackage} disabled={!facebookPackage}>
                  <Copy className="mr-2 h-4 w-4" />Copy Facebook Post
                </Button>
              )}
              {publishingMode === 'branded-graphic' && graphicType === 'newsletter' && (
                <Button type="button" variant="default" onClick={copyNewsletterPost} disabled={!newsletterPost}>
                  <Copy className="mr-2 h-4 w-4" />Copy Newsletter Post
                </Button>
              )}
              <Button type="button" variant="outline" onClick={copyFacebookCaption} disabled={!activeCaption}>
                <Copy className="mr-2 h-4 w-4" />Copy Caption
              </Button>
              <Button type="button" variant="outline" onClick={copyHashtags} disabled={!activeHashtags}>
                <Copy className="mr-2 h-4 w-4" />Copy Hashtags
              </Button>
            </div>
          </section>
          {publishingMode === 'branded-graphic' && (
            <>
              <section aria-labelledby="facebook-dialog-graphic-type-label">
                <h3 id="facebook-dialog-graphic-type-label" className="mb-2 text-sm font-semibold">Graphic Type</h3>
                <div role="radiogroup" aria-labelledby="facebook-dialog-graphic-type-label" className="flex flex-wrap gap-2">
                  {GRAPHIC_TYPES.map(type => (
                    <label key={type.value} className="flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-sm focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
                      <input
                        type="radio"
                        name="facebook-graphic-type"
                        value={type.value}
                        checked={graphicType === type.value}
                        onChange={() => changeGraphicType(type.value)}
                      />
                      <span>{type.label}</span>
                    </label>
                  ))}
                </div>
              </section>
              {graphicType === 'breaking-news' && (
                <section aria-label="Breaking News confirmation" className="rounded-md border border-red-200 bg-red-50 p-3">
                  <label className="flex items-start gap-2 text-sm font-medium text-red-900">
                    <input
                      type="checkbox"
                      checked={breakingConfirmed}
                      onChange={event => setBreakingConfirmed(event.target.checked)}
                    />
                    I confirm this is genuinely breaking news
                  </label>
                </section>
              )}
              {graphicType === 'quote' && (
                <section aria-label="Verified quote details" className="space-y-3 rounded-md border p-3">
                  <p className="text-sm text-muted-foreground">Use only a verified quotation from the article or source material.</p>
                  <label className="block text-sm font-medium">
                    Quote
                    <textarea aria-label="Verified quote" maxLength={240} value={quoteText} onChange={event => setQuoteText(event.target.value)} className="mt-1 min-h-20 w-full rounded-md border p-2" />
                  </label>
                  <label className="block text-sm font-medium">
                    Attribution
                    <input aria-label="Quote attribution" maxLength={80} value={quoteAttribution} onChange={event => setQuoteAttribution(event.target.value)} className="mt-1 w-full rounded-md border p-2" />
                  </label>
                  <p className="text-xs text-muted-foreground">Quote maximum 240 characters; attribution maximum 80 characters.</p>
                </section>
              )}
              {graphicType === 'poll' && (
                <section aria-label="Poll details" className="space-y-3 rounded-md border p-3">
                  <p className="text-sm text-muted-foreground">Add the actual Facebook poll or ask readers to reply in comments.</p>
                  <label className="block text-sm font-medium">Question<input aria-label="Poll question" maxLength={140} value={pollQuestion} onChange={event => setPollQuestion(event.target.value)} className="mt-1 w-full rounded-md border p-2" /></label>
                  <label className="block text-sm font-medium">Option A<input aria-label="Poll option A" maxLength={48} value={pollOptionA} onChange={event => setPollOptionA(event.target.value)} className="mt-1 w-full rounded-md border p-2" /></label>
                  <label className="block text-sm font-medium">Option B<input aria-label="Poll option B" maxLength={48} value={pollOptionB} onChange={event => setPollOptionB(event.target.value)} className="mt-1 w-full rounded-md border p-2" /></label>
                  <p className="text-xs text-muted-foreground">Question maximum 140 characters; each option maximum 48 characters.</p>
                </section>
              )}
              <section aria-labelledby="facebook-dialog-graphic-actions">
                <h3 id="facebook-dialog-graphic-actions" className="mb-2 text-sm font-semibold">Graphics</h3>
                <div className="flex flex-wrap gap-2">
                  <Button type="button" variant={previewUrl ? 'outline' : 'default'} onClick={generate} disabled={loading || downloading || !canGenerate}>
                    {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /><span role="status" aria-live="polite">Generating…</span></> : previewUrl ? <><RefreshCw className="mr-2 h-4 w-4" />Regenerate</> : <><ImageIcon className="mr-2 h-4 w-4" />Generate Graphic</>}
                  </Button>
                  <Button type="button" variant="outline" onClick={download} disabled={!previewUrl || loading || downloading}>
                    {downloading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /><span role="status" aria-live="polite">Creating PNG…</span></> : <><Download className="mr-2 h-4 w-4" />Download Graphic</>}
                  </Button>
                </div>
              </section>
            </>
          )}
          <div className="flex justify-end">
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>Close</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};


export default FacebookLocalGraphicDialog;
