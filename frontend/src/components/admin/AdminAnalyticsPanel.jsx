import React from 'react';
import { AlertCircle, BarChart3, Loader2 } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { buildArticleUrl } from '../../utils/articleUrl';


const PERIODS = [
  ['today', 'Today'],
  ['week', 'This week'],
  ['month', 'This month'],
];


const AdminAnalyticsPanel = ({ period, onPeriodChange, loading, error, summary }) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-purple-600" />
        Analytics
      </CardTitle>
      <CardDescription>
        First-party performance across articles, newsletter and commercial activity
      </CardDescription>
      <div className="flex flex-wrap gap-2 pt-3" role="group" aria-label="Analytics period">
        {PERIODS.map(([value, label]) => (
          <Button
            key={value}
            type="button"
            size="sm"
            variant={period === value ? 'default' : 'outline'}
            onClick={() => onPeriodChange(value)}
            aria-pressed={period === value}
            data-testid={`analytics-period-${value}`}
          >
            {label}
          </Button>
        ))}
      </div>
    </CardHeader>
    <CardContent>
      {loading ? (
        <div className="text-center py-10" role="status" aria-live="polite">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-purple-600" />
          <p className="mt-2 text-muted-foreground">Loading analytics…</p>
        </div>
      ) : error ? (
        <div className="text-center py-10" role="alert" data-testid="analytics-unavailable">
          <AlertCircle className="h-10 w-10 mx-auto mb-3 text-amber-500" />
          <p className="font-medium">Analytics are temporarily unavailable.</p>
          <p className="text-sm text-muted-foreground mt-1">No publishing or reader-facing feature is affected.</p>
        </div>
      ) : summary ? (
        <div className="space-y-6" data-testid="analytics-dashboard">
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            {summary.article_views?.available ? (
              <>
                <div className="bg-purple-50 dark:bg-purple-950/30 rounded-lg p-4">
                  <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">{summary.article_views.total}</p>
                  <p className="text-sm text-purple-600 dark:text-purple-400">Article views</p>
                </div>
                <div className="bg-blue-50 dark:bg-blue-950/30 rounded-lg p-4">
                  <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{summary.article_views.unique_articles}</p>
                  <p className="text-sm text-blue-600 dark:text-blue-400">Articles read</p>
                </div>
              </>
            ) : (
              <div className="col-span-2 rounded-lg border p-4 text-sm text-muted-foreground">Article analytics unavailable</div>
            )}
            {summary.newsletter?.available ? (
              <>
                <div className="bg-emerald-50 dark:bg-emerald-950/30 rounded-lg p-4">
                  <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">{summary.newsletter.opens}</p>
                  <p className="text-sm text-emerald-600 dark:text-emerald-400">Newsletter opens</p>
                </div>
                <div className="bg-indigo-50 dark:bg-indigo-950/30 rounded-lg p-4">
                  <p className="text-2xl font-bold text-indigo-700 dark:text-indigo-300">{summary.newsletter.clicks}</p>
                  <p className="text-sm text-indigo-600 dark:text-indigo-400">Newsletter clicks</p>
                </div>
              </>
            ) : (
              <div className="col-span-2 rounded-lg border p-4 text-sm text-muted-foreground">Newsletter analytics unavailable</div>
            )}
            {summary.facebook?.available ? (
              <div className="bg-sky-50 dark:bg-sky-950/30 rounded-lg p-4">
                <p className="text-2xl font-bold text-sky-700 dark:text-sky-300">{summary.facebook.facebook_views}</p>
                <p className="text-sm text-sky-600 dark:text-sky-400">Facebook article views</p>
              </div>
            ) : (
              <div className="rounded-lg border p-4 text-sm text-muted-foreground">Facebook attribution unavailable</div>
            )}
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <section aria-labelledby="most-read-heading">
              <h3 id="most-read-heading" className="font-semibold mb-3">Most-read content</h3>
              {!summary.article_views?.available ? (
                <p className="text-sm text-muted-foreground">Article analytics unavailable.</p>
              ) : summary.article_views.top_articles?.filter(
                (article) => article.archived !== true && article.manual_review_hidden_from_public !== true
              ).length ? (
                <ol className="space-y-3">
                  {summary.article_views.top_articles
                    .filter((article) => article.archived !== true && article.manual_review_hidden_from_public !== true)
                    .map((article, index) => (
                    <li key={article.id} className="flex gap-3 rounded-lg border p-3">
                      <span className="font-semibold text-muted-foreground">{index + 1}</span>
                      <div className="min-w-0 flex-1">
                        <a
                          href={buildArticleUrl(article)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-blue-700 dark:text-blue-300 hover:underline"
                        >
                          {article.title}
                        </a>
                        <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
                          <Badge variant="outline">{article.category}</Badge>
                          <span>{article.views} views</span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-sm text-muted-foreground" data-testid="analytics-empty">No article views were recorded for this period.</p>
              )}
            </section>

            <section aria-labelledby="category-performance-heading">
              <h3 id="category-performance-heading" className="font-semibold mb-3">Category performance</h3>
              {!summary.article_views?.available ? (
                <p className="text-sm text-muted-foreground">Category analytics unavailable.</p>
              ) : summary.article_views.categories?.length ? (
                <div className="space-y-3">
                  {summary.article_views.categories.map((row) => (
                    <div key={row.category}>
                      <div className="flex justify-between gap-3 text-sm mb-1">
                        <span>{row.category}</span>
                        <span>{row.views} views · {row.share_percent}%</span>
                      </div>
                      <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                        <div className="h-full bg-purple-600" style={{ width: `${Math.min(100, row.share_percent)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No category activity was recorded for this period.</p>
              )}
            </section>
          </div>

          <section aria-labelledby="facebook-driven-heading">
            <h3 id="facebook-driven-heading" className="font-semibold mb-3">Top Facebook-driven articles</h3>
            {!summary.facebook?.available ? (
              <p className="text-sm text-muted-foreground">Facebook attribution unavailable.</p>
            ) : summary.facebook.top_facebook_articles?.length ? (
              <ol className="grid gap-3 md:grid-cols-2">
                {summary.facebook.top_facebook_articles.slice(0, 5).map((article, index) => (
                  <li key={article.id} className="flex gap-3 rounded-lg border p-3">
                    <span className="font-semibold text-muted-foreground">{index + 1}</span>
                    <div className="min-w-0 flex-1">
                      <a href={buildArticleUrl(article)} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-700 dark:text-blue-300 hover:underline">
                        {article.title}
                      </a>
                      <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline">{article.category}</Badge>
                        <span>{article.views} Facebook views</span>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-muted-foreground" data-testid="facebook-analytics-empty">No Facebook-attributed article views were recorded for this period.</p>
            )}
          </section>

          <div className="grid lg:grid-cols-2 gap-6">
            <section className="rounded-lg border p-4" aria-labelledby="newsletter-summary-heading">
              <h3 id="newsletter-summary-heading" className="font-semibold mb-3">Newsletter summary</h3>
              {summary.newsletter?.available ? (
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div><dt className="text-muted-foreground">Provider-accepted opportunities</dt><dd className="text-xl font-semibold">{summary.newsletter.accepted_opportunities}</dd></div>
                  <div><dt className="text-muted-foreground">Accepted send batches</dt><dd className="text-xl font-semibold">{summary.newsletter.send_batches}</dd></div>
                  <div><dt className="text-muted-foreground">Open events</dt><dd className="text-xl font-semibold">{summary.newsletter.opens}</dd></div>
                  <div><dt className="text-muted-foreground">Click events</dt><dd className="text-xl font-semibold">{summary.newsletter.clicks}</dd></div>
                </dl>
              ) : (
                <p className="text-sm text-muted-foreground">Newsletter analytics unavailable.</p>
              )}
            </section>

            <section className="rounded-lg border p-4" aria-labelledby="commercial-summary-heading">
              <h3 id="commercial-summary-heading" className="font-semibold mb-3">Commercial summary</h3>
              <div className="space-y-4">
                {summary.sponsored?.available ? (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Sponsored placement lifetime counters</p>
                    <dl className="grid grid-cols-3 gap-3 text-sm">
                      <div><dt className="text-muted-foreground">Impressions</dt><dd className="text-xl font-semibold">{summary.sponsored.impressions}</dd></div>
                      <div><dt className="text-muted-foreground">Clicks</dt><dd className="text-xl font-semibold">{summary.sponsored.clicks}</dd></div>
                      <div><dt className="text-muted-foreground">CTR</dt><dd className="text-xl font-semibold">{summary.sponsored.ctr_percent == null ? '—' : `${summary.sponsored.ctr_percent}%`}</dd></div>
                    </dl>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Sponsored placement analytics unavailable.</p>
                )}
                {summary.advertisers?.available ? (
                  <div className="border-t pt-3">
                    <p className="text-sm text-muted-foreground">Advertiser leads created in this period</p>
                    <p className="text-xl font-semibold">{summary.advertisers.total}</p>
                    {summary.advertisers.by_status?.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {summary.advertisers.by_status.map((row) => (
                          <Badge key={row.status} variant="outline">{row.status}: {row.count}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Advertiser lead analytics unavailable.</p>
                )}
              </div>
            </section>
          </div>
        </div>
      ) : null}
    </CardContent>
  </Card>
);


export default AdminAnalyticsPanel;
