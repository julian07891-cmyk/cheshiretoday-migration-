import fs from 'fs';
import path from 'path';


const dashboardSource = fs.readFileSync(
  path.join(__dirname, '..', 'components', 'AdminDashboard.jsx'),
  'utf8'
);


test('quick actions use the current operational labels', () => {
  [
    'Run Hybrid Import',
    'Send Daily Brief',
    'Post to Facebook',
    'Post to Twitter',
    'Remove Duplicates',
    'Archive Legacy Content',
    'Remove Product Articles',
    'Run RSS Sync',
  ].forEach(label => expect(dashboardSource).toContain(`<span>${label}</span>`));

  [
    '<span>Generate</span>',
    '<span>Daily Brief</span>',
    '<span>Cleanup</span>',
    '<span>No Products</span>',
    '<span>Sync RSS</span>',
  ].forEach(label => expect(dashboardSource).not.toContain(label));
});


test('mobile tabs use clear labels and retain scroll-safe layout', () => {
  ['Newsletter', 'Facebook', 'Email', 'Analytics', 'Affiliates'].forEach(
    label => expect(dashboardSource).toContain(`<span>${label}</span>`)
  );

  ['Subs', 'FB', 'Digest', 'Stats', 'Affil'].forEach(
    label => expect(dashboardSource).not.toContain(`<span>${label}</span>`)
  );

  expect(dashboardSource).toContain(
    'flex gap-1 overflow-x-auto pb-1 scrollbar-thin'
  );
  expect(dashboardSource.match(/min-w-fit/g).length).toBeGreaterThanOrEqual(9);
});


test('import panel describes filtering and outcomes without quota promises', () => {
  [
    'Run News Import',
    'Check current RSS and research sources for suitable Cheshire Today stories.',
    'Prioritises Cheshire local reporting',
    'Includes business, finance and AI &amp; Tech coverage',
    'Applies duplicate, image, locality and quality checks',
    'Strong articles may publish; others are sent to Manual Review',
    'Results depend on current source availability',
  ].forEach(copy => expect(dashboardSource).toContain(copy));

  expect(dashboardSource).not.toMatch(/~8 Cheshire|~12 UK|Sports is capped|≤3/);
});


test('maintenance and editorial sections use accurate reader-facing copy', () => {
  expect(dashboardSource).toContain('Archive All &amp; Run Fresh Import');
  expect(dashboardSource).toContain(
    'This is a broad maintenance action. Existing articles remain available in the archive.'
  );
  expect(dashboardSource).toContain('Recalculate Article Locations');
  expect(dashboardSource).toContain('Recalculate Locations');
  expect(dashboardSource).toContain(
    'articles withheld from public publication pending editorial review'
  );
  expect(dashboardSource).toContain('Create OpenAI Draft');
  expect(dashboardSource).toContain('<CardTitle>Article Archive</CardTitle>');
});


test('quick action layout wraps labels without reducing touch height', () => {
  expect(dashboardSource).toContain(
    "const QUICK_ACTION_BUTTON_LAYOUT = 'min-h-12 h-auto px-2 py-2"
  );
  expect(dashboardSource).toContain('leading-tight whitespace-normal');
  expect(
    dashboardSource.split('${QUICK_ACTION_BUTTON_LAYOUT}').length - 1
  ).toBe(9);
});


test('reviewed handlers and endpoint paths remain unchanged', () => {
  [
    'onClick={handleGenerateArticles}',
    'onClick={handleSendDigest}',
    'onClick={handlePostToFacebook}',
    'onClick={handlePostToTwitter}',
    'onClick={handleCleanupDuplicates}',
    'onClick={handleFixMismatchedContent}',
    'onClick={handleRemoveProductArticles}',
    'onClick={handleSyncRSS}',
    'onClick={handleImportNews}',
    'onClick={handleClearAndRefresh}',
    'onClick={handleBackfillLocations}',
  ].forEach(handler => expect(dashboardSource).toContain(handler));

  [
    '/api/generate-articles',
    '/api/send-digest',
    '/api/facebook/trigger-scheduled',
    '/api/twitter/trigger-scheduled',
    '/api/admin/remove-duplicates',
    '/api/fix-mismatched-content',
    '/api/remove-product-articles',
    '/api/sync-rss-now',
    '/api/import-hybrid-news',
    '/api/admin/clear-and-refresh',
    '/api/admin/backfill-locations',
  ].forEach(endpoint => expect(dashboardSource).toContain(endpoint));
});


test('source descriptions omit stale policy claims', () => {
  expect(dashboardSource).not.toContain('Manchester Evening News');
  expect(dashboardSource).not.toContain('Email Strategy (January 2026)');
  expect(dashboardSource).toContain('Filtered Cheshire town and council searches');
  expect(dashboardSource).toContain('Guardian money and finance coverage');
});
