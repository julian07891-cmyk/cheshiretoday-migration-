import fs from 'fs';
import path from 'path';

import {
  archiveSelectedArticles,
  formatImportCompletion,
  removeArchivedSelection,
} from './adminArticleActions';


const buildArchiveRequest = ({
  selectedIds = ['article-a', 'article-b'],
  confirmed = true,
  responses = [true, true],
} = {}) => {
  const confirmAction = jest.fn().mockResolvedValue(confirmed);
  const onConfirmed = jest.fn();
  const fetchImpl = jest.fn();

  responses.forEach(ok => {
    if (ok instanceof Error) {
      fetchImpl.mockRejectedValueOnce(ok);
    } else {
      fetchImpl.mockResolvedValueOnce({ ok });
    }
  });

  return {
    confirmAction,
    fetchImpl,
    onConfirmed,
    execute: () => archiveSelectedArticles({
      selectedIds,
      apiUrl: 'https://admin-api.example',
      authHeaders: { Authorization: 'Bearer admin-test-token' },
      confirmAction,
      fetchImpl,
      onConfirmed,
    }),
  };
};


test('selected archive confirms the count and cancellation makes no request', async () => {
  const request = buildArchiveRequest({ confirmed: false });

  const result = await request.execute();

  expect(result).toEqual({ status: 'cancelled' });
  expect(request.confirmAction).toHaveBeenCalledWith({
    title: 'Archive 2 Selected Articles',
    description: 'Archive 2 selected article(s)? They will remain available in the archive.',
    variant: 'warning',
    confirmText: 'Archive Selected',
    cancelText: 'Cancel',
  });
  expect(request.fetchImpl).not.toHaveBeenCalled();
  expect(request.onConfirmed).not.toHaveBeenCalled();
});


test('each selected ID uses the authenticated POST archive endpoint once', async () => {
  const request = buildArchiveRequest();

  const result = await request.execute();

  expect(result).toEqual({
    status: 'success',
    archivedIds: ['article-a', 'article-b'],
    failedIds: [],
    message: 'Archived 2 selected articles.',
  });
  expect(request.fetchImpl).toHaveBeenCalledTimes(2);
  expect(request.fetchImpl).toHaveBeenNthCalledWith(
    1,
    'https://admin-api.example/api/admin/articles/article-a/archive',
    {
      method: 'POST',
      headers: { Authorization: 'Bearer admin-test-token' },
    }
  );
  expect(request.fetchImpl).toHaveBeenNthCalledWith(
    2,
    'https://admin-api.example/api/admin/articles/article-b/archive',
    {
      method: 'POST',
      headers: { Authorization: 'Bearer admin-test-token' },
    }
  );
  for (const [, options] of request.fetchImpl.mock.calls) {
    expect(options.method).not.toBe('DELETE');
  }
  expect(request.onConfirmed).toHaveBeenCalledTimes(1);
});


test('partial archive reports aggregate counts without private failures', async () => {
  const request = buildArchiveRequest({
    responses: [true, new Error('private database exception')],
  });

  const result = await request.execute();

  expect(result).toEqual({
    status: 'partial',
    archivedIds: ['article-a'],
    failedIds: ['article-b'],
    message: 'Archived 1 articles. 1 could not be archived.',
  });
  expect(JSON.stringify(result)).not.toContain('private database exception');
});


test('complete archive failure is private and fail-safe', async () => {
  const request = buildArchiveRequest({ responses: [false, false] });

  const result = await request.execute();

  expect(result).toEqual({
    status: 'error',
    archivedIds: [],
    failedIds: ['article-a', 'article-b'],
    message: 'Could not archive the selected articles. Please try again.',
  });
});


test('only successfully archived IDs are cleared from selection', () => {
  const remaining = removeArchivedSelection(
    new Set(['article-a', 'article-b', 'article-c']),
    ['article-a', 'article-c']
  );

  expect(Array.from(remaining)).toEqual(['article-b']);
});


test.each([
  {
    name: 'public-only',
    result: {
      public_imported: 3,
      manual_review_imported: 0,
      total_imported: 3,
    },
    message: 'Import completed: 3 public articles added, 0 sent to Manual Review, 3 total retained.',
  },
  {
    name: 'manual-review-only',
    result: {
      public_imported: 0,
      manual_review_imported: 2,
      total_imported: 2,
    },
    message: 'Import completed: no public articles were added; 2 articles were sent to Manual Review.',
  },
  {
    name: 'mixed',
    result: {
      public_imported: 4,
      manual_review_imported: 2,
      total_imported: 6,
    },
    message: 'Import completed: 4 public articles added, 2 sent to Manual Review, 6 total retained.',
  },
  {
    name: 'zero-retained',
    result: {
      public_imported: 0,
      manual_review_imported: 0,
      total_imported: 0,
    },
    message: 'Import completed: no new articles were retained. Existing duplicates, source filters, image requirements or quality checks may have excluded the available candidates.',
  },
])('$name import result always has an explicit completion message', ({ result, message }) => {
  expect(formatImportCompletion(result).message).toBe(message);
});


test('import cost is exposed only when it is a valid number', () => {
  expect(formatImportCompletion({ estimated_cost_usd: 0.1234 }).estimatedCost)
    .toBe(0.1234);
  expect(formatImportCompletion({ estimated_cost_usd: '0.1234' }).estimatedCost)
    .toBeNull();
  expect(formatImportCompletion({ estimated_cost_usd: Number.NaN }).estimatedCost)
    .toBeNull();
});


test('import completion does not invent unavailable rejection counts', () => {
  const completion = formatImportCompletion({
    public_imported: 1,
    manual_review_imported: 1,
    total_imported: 2,
  });

  expect(completion).not.toHaveProperty('duplicates');
  expect(completion).not.toHaveProperty('rejected');
  expect(completion.message).not.toMatch(/\\d+ duplicates|\\d+ rejected/i);
});

test('inconsistent total does not override the detailed component sum', () => {
  const completion = formatImportCompletion({
    public_imported: 2,
    manual_review_imported: 3,
    total_imported: 99,
  });

  expect(completion.retained).toBe(5);
  expect(completion.message).toBe(
    'Import completed: 2 public articles added, 3 sent to Manual Review, 5 total retained.'
  );
});


test('legacy total-only response retains its compatible count', () => {
  const completion = formatImportCompletion({ total_imported: 4 });

  expect(completion.retained).toBe(4);
  expect(completion.message).toContain('4 total retained');
});


test('invalid detailed fields safely fall back to the compatible total', () => {
  const completion = formatImportCompletion({
    public_imported: '2',
    manual_review_imported: -1,
    total_imported: 6,
  });

  expect(completion.publicImported).toBe(0);
  expect(completion.manualReviewImported).toBe(0);
  expect(completion.retained).toBe(6);
});


test('Admin wiring refreshes accepted archive results and uses corrected result fields', () => {
  const dashboardSource = fs.readFileSync(
    path.join(__dirname, '..', 'components', 'AdminDashboard.jsx'),
    'utf8'
  );

  expect(dashboardSource).toContain('onClick={handleArchiveSelectedArticles}');
  expect(dashboardSource).toContain('fetchArchivedArticles()');
  expect(dashboardSource).toContain('fetchArticleStats()');
  expect(dashboardSource).toContain('removeArchivedSelection(');
  expect(dashboardSource).toContain('data.articles_archived');
  expect(dashboardSource).not.toContain('data.articles_fixed');
  expect(dashboardSource).toContain(
    'Archived ${data.articles_archived} legacy template-mismatch articles.'
  );
  expect(dashboardSource).toContain('Archive Legacy Content');
  expect(dashboardSource).not.toContain('Fix Content');
});


test('article archival controls no longer claim deletion while genuine deletes remain', () => {
  const dashboardSource = fs.readFileSync(
    path.join(__dirname, '..', 'components', 'AdminDashboard.jsx'),
    'utf8'
  );

  expect(dashboardSource).not.toContain("title: 'Delete Article'");
  expect(dashboardSource).not.toContain("title: 'Delete Manual Review Article'");
  expect(dashboardSource).not.toContain('Delete Selected ({selectedManualReviewArticles.size})');
  expect(dashboardSource).toContain("title: 'Archive Article'");
  expect(dashboardSource).toContain("title: 'Archive Manual Review Article'");

  expect(dashboardSource).toContain('Delete this job listing?');
  expect(dashboardSource).toContain('Delete product');
  expect(dashboardSource).toContain('Delete advert');
  expect(dashboardSource).toContain('Delete lead');
});
