import fs from 'fs';
import path from 'path';


const dashboardSource = fs.readFileSync(
  path.join(__dirname, '..', 'components', 'AdminDashboard.jsx'),
  'utf8'
);


test('subscriber rows use the management-ID soft-unsubscribe contract', () => {
  const handlerStart = dashboardSource.indexOf(
    'const handleUnsubscribeSubscriber'
  );
  const handlerEnd = dashboardSource.indexOf(
    'const formatDate',
    handlerStart
  );
  const handler = dashboardSource.slice(handlerStart, handlerEnd);

  expect(handler).toContain('handleUnsubscribeSubscriber');
  expect(handler).toContain(
    '/api/admin/subscribers/${encodeURIComponent(newsletterManagementId)}/unsubscribe'
  );
  expect(handler).toContain("method: 'POST'");
  expect(handler).toContain('headers: getAuthHeaders()');
  expect(handler).not.toContain(
    '/api/admin/subscribers/${encodeURIComponent(email)}'
  );
  expect(handler).not.toContain("method: 'DELETE'");
});


test('unsubscribe confirmation and user-facing results are privacy safe', () => {
  expect(dashboardSource).toContain(
    'Unsubscribe this subscriber? They will stop receiving all newsletter emails. Their preferences and subscription history will be retained.'
  );
  expect(dashboardSource).toContain('Subscriber unsubscribed.');
  expect(dashboardSource).toContain(
    'Could not unsubscribe subscriber. Please try again.'
  );
  expect(dashboardSource).not.toContain('Subscriber Removed');
  expect(dashboardSource).not.toContain('Failed to remove subscriber');
});


test('cancellation occurs before loading or network work', () => {
  const handlerStart = dashboardSource.indexOf(
    'const handleUnsubscribeSubscriber'
  );
  const handlerEnd = dashboardSource.indexOf(
    'const formatDate',
    handlerStart
  );
  const handler = dashboardSource.slice(handlerStart, handlerEnd);

  expect(handler.indexOf('if (!confirmed) return;')).toBeGreaterThan(-1);
  expect(handler.indexOf('if (!confirmed) return;')).toBeLessThan(
    handler.indexOf('setActionLoading')
  );
  expect(handler.indexOf('if (!confirmed) return;')).toBeLessThan(
    handler.indexOf('await fetch(')
  );
});


test('successful unsubscribe refreshes data without removing the row locally', () => {
  const handlerStart = dashboardSource.indexOf(
    'const handleUnsubscribeSubscriber'
  );
  const handlerEnd = dashboardSource.indexOf(
    'const formatDate',
    handlerStart
  );
  const handler = dashboardSource.slice(handlerStart, handlerEnd);

  expect(handler).toContain('await fetchAllData();');
  expect(handler).not.toContain('setSubscribers(');
  expect(handler).not.toContain('.filter(');
});


test('subscriber state and reversible lifecycle guidance are visible', () => {
  expect(dashboardSource).toContain(
    "{subscriber.active === false ? 'Unsubscribed' : 'Active'}"
  );
  expect(dashboardSource).toContain(
    'Reactivation requires a verified email link.'
  );
  expect(dashboardSource).toContain(
    'title="Unsubscribe subscriber"'
  );
  expect(dashboardSource).toContain(
    'aria-label="Unsubscribe subscriber"'
  );
  expect(dashboardSource).toContain('<UserMinus className="h-4 w-4" />');
});


test('already inactive subscribers have no unsubscribe control', () => {
  expect(dashboardSource).toContain(
    '{subscriber.active !== false'
  );
  expect(dashboardSource).toContain(
    'data-testid={`unsubscribe-subscriber-${subscriber.newsletter_management_id}`}'
  );
  expect(dashboardSource).not.toContain('data-testid={`delete-subscriber-');
});


test('valid active subscribers retain the management-ID action', () => {
  expect(dashboardSource).toContain(
    'const CANONICAL_NEWSLETTER_MANAGEMENT_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;'
  );
  expect(dashboardSource).toContain(
    "CANONICAL_NEWSLETTER_MANAGEMENT_ID_PATTERN.test(\n                          subscriber.newsletter_management_id || ''\n                        ) && ("
  );
  expect(dashboardSource).toContain(
    'onClick={() => handleUnsubscribeSubscriber(\n                            subscriber.newsletter_management_id\n                          )}'
  );
});


test('active subscribers without a valid management ID receive guidance', () => {
  expect(dashboardSource).toContain(
    "Management ID unavailable — subscriber migration or repair is required."
  );
  expect(dashboardSource).toContain(
    "data-testid={`subscriber-management-id-guidance-${subscriber.email}`}"
  );
  expect(dashboardSource).toContain(
    "!CANONICAL_NEWSLETTER_MANAGEMENT_ID_PATTERN.test(\n                              subscriber.newsletter_management_id || ''\n                            ) && ("
  );
});


test('missing management IDs cannot reach a network action or legacy fallback', () => {
  const subscriberRowsStart = dashboardSource.indexOf(
    "{subscribers.map((subscriber) => ("
  );
  const subscriberRowsEnd = dashboardSource.indexOf(
    "{activeTab === 'facebook'",
    subscriberRowsStart
  );
  const subscriberRows = dashboardSource.slice(
    subscriberRowsStart,
    subscriberRowsEnd
  );

  expect(subscriberRows.indexOf(
    'CANONICAL_NEWSLETTER_MANAGEMENT_ID_PATTERN.test'
  )).toBeLessThan(
    subscriberRows.indexOf('onClick={() => handleUnsubscribeSubscriber(')
  );
  expect(subscriberRows).not.toContain('handleDeleteSubscriber');
  expect(subscriberRows).not.toContain("method: 'DELETE'");
  expect(subscriberRows).not.toContain('encodeURIComponent(subscriber.email)');
});
