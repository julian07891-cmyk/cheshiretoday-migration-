import fs from 'fs';
import path from 'path';

import { runBulkArchive } from './adminBulkArchive';


const buildRequest = ({
  daysOld,
  confirmed = true,
  response = {
    ok: true,
    json: async () => ({ success: true, archived_count: 4 }),
  },
  fetchImpl = jest.fn().mockResolvedValue(response),
} = {}) => {
  const confirmAction = jest.fn().mockReturnValue(confirmed);
  const onConfirmed = jest.fn();

  return {
    fetchImpl,
    confirmAction,
    onConfirmed,
    execute: () => runBulkArchive({
      daysOld,
      apiUrl: 'https://admin-api.example',
      authHeaders: { Authorization: 'Bearer test-admin-token' },
      confirmAction,
      fetchImpl,
      onConfirmed,
    }),
  };
};


describe.each([7, 14, 30])('Bulk Archive %i-day request', (daysOld) => {
  test('uses the authenticated JSON body contract', async () => {
    const request = buildRequest({ daysOld });

    const result = await request.execute();

    expect(result.status).toBe('success');
    expect(request.confirmAction).toHaveBeenCalledWith(
      `Archive articles older than ${daysOld} days? They will remain available in the archive.`
    );
    expect(request.fetchImpl).toHaveBeenCalledTimes(1);
    expect(request.fetchImpl).toHaveBeenCalledWith(
      'https://admin-api.example/api/admin/articles/bulk-archive',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer test-admin-token',
        },
        body: JSON.stringify({ days_old: daysOld }),
      }
    );
    expect(request.fetchImpl.mock.calls[0][0]).not.toContain('days_old=');
    expect(request.onConfirmed).toHaveBeenCalledTimes(1);
  });
});


test('cancelling confirmation sends no request', async () => {
  const request = buildRequest({ daysOld: 7, confirmed: false });

  const result = await request.execute();

  expect(result).toEqual({ status: 'cancelled' });
  expect(request.fetchImpl).not.toHaveBeenCalled();
  expect(request.onConfirmed).not.toHaveBeenCalled();
});


test('success message uses the requested threshold and actual archived count', async () => {
  const request = buildRequest({
    daysOld: 14,
    response: {
      ok: true,
      json: async () => ({ success: true, archived_count: 3 }),
    },
  });

  const result = await request.execute();

  expect(result).toEqual({
    status: 'success',
    archivedCount: 3,
    message: 'Archived 3 articles older than 14 days.',
  });
  expect(result.message.toLowerCase()).toContain('archive');
  expect(result.message.toLowerCase()).not.toContain('delete');
});


test('single-article success message remains grammatical and archive-only', async () => {
  const request = buildRequest({
    daysOld: 30,
    response: {
      ok: true,
      json: async () => ({ success: true, archived_count: 1 }),
    },
  });

  const result = await request.execute();

  expect(result.message).toBe('Archived 1 article older than 30 days.');
  expect(result.message.toLowerCase()).not.toContain('delete');
});


test.each([
  {
    response: {
      ok: false,
      json: async () => ({ detail: 'private database failure' }),
    },
  },
  {
    response: {
      ok: true,
      json: async () => {
        throw new Error('private malformed response');
      },
    },
  },
  {
    fetchImpl: jest.fn().mockRejectedValue(
      new Error('private network exception')
    ),
  },
])('failures return one safe human-readable message', async (options) => {
  const request = buildRequest({ daysOld: 7, ...options });

  const result = await request.execute();

  expect(result).toEqual({
    status: 'error',
    message: 'Could not archive articles. Please try again.',
  });
  expect(JSON.stringify(result)).not.toMatch(
    /private database|private malformed|private network/i
  );
});


test('the three visible controls remain wired to the reviewed thresholds', () => {
  const dashboardSource = fs.readFileSync(
    path.join(__dirname, '..', 'components', 'AdminDashboard.jsx'),
    'utf8'
  );

  expect(dashboardSource).toContain('handleBulkArchive(7)');
  expect(dashboardSource).toContain('handleBulkArchive(14)');
  expect(dashboardSource).toContain('handleBulkArchive(30)');
  expect(dashboardSource).toContain('runBulkArchive({');
  expect(dashboardSource).not.toContain(
    'bulk-archive?days_old=${daysOld}'
  );
});
