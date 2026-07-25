import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

import ManualReviewEditorialMetadata from './ManualReviewEditorialMetadata';


describe('ManualReviewEditorialMetadata', () => {
  let container;
  let root;

  beforeAll(() => {
    global.IS_REACT_ACT_ENVIRONMENT = true;
  });

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  test('renders concise editorial metadata without changing article actions', () => {
    act(() => {
      root.render(
        <ManualReviewEditorialMetadata
          metadata={{
            publication_recommendation: 'Needs rewrite',
            editorial_topic: 'Community feature',
            detected_locality: 'Chester',
            source_type: 'local_rss',
            rewrite_status: 'manual_review_required',
            rewrite_length: 842,
            image_status: 'available',
            freshness_bucket: 'recent',
            failed_public_gate: 'content_length',
            duplicate_status: 'not_flagged',
            auto_publish_candidate: false,
          }}
        />
      );
    });

    expect(container.textContent).toContain('Needs rewrite');
    expect(container.textContent).toContain('Community feature');
    expect(container.textContent).toContain('Chester');
    expect(container.textContent).toContain('842 characters');
    expect(container.textContent).toContain('Manual review required');
    expect(container.textContent).toContain('Not flagged');
    expect(container.textContent).toContain('Content length');
    expect(container.textContent).toContain('Not an automatic publish candidate');
  });

  test('renders nothing for an older record when metadata is unavailable', () => {
    act(() => root.render(<ManualReviewEditorialMetadata metadata={null} />));
    expect(container.innerHTML).toBe('');
  });
});
