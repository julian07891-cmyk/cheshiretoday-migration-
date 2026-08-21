import {
  CONTEXTUAL_RECOMMENDATIONS,
  isContextualRecommendationRegistryBounded,
  normaliseContextualCategory,
  selectContextualRecommendation,
} from './contextualRecommendations';


const eligibleArticle = {
  category: 'Business & Finance',
  title: 'Small firms compare accounting software ahead of tax changes',
  summary: 'Local companies are reviewing bookkeeping tools for VAT and invoicing.',
  tags: ['small business', 'QuickBooks'],
};


describe('contextual recommendation targeting', () => {
  test('selects the single approved guide for a strong eligible article', () => {
    const recommendation = selectContextualRecommendation(eligibleArticle);

    expect(recommendation).toBe(CONTEXTUAL_RECOMMENDATIONS[0]);
    expect(recommendation.destination_url).toBe('/guides/best-accounting-software-uk');
    expect(CONTEXTUAL_RECOMMENDATIONS).toHaveLength(1);
  });

  test.each([
    [{ ...eligibleArticle, category: 'Sport' }, 'unrelated category'],
    [{ ...eligibleArticle, title: 'Business confidence improves', summary: 'Hiring rose.', tags: [] }, 'no explicit topic'],
    [{ ...eligibleArticle, category: 'Unknown desk' }, 'unknown category'],
    [null, 'missing article'],
    ['malformed', 'malformed article'],
  ])('fails closed for %s', (article) => {
    expect(selectContextualRecommendation(article)).toBeNull();
  });

  test.each([
    'A fatal crash affects an accounting software company',
    'Court sentences director of a bookkeeping software firm',
    'Missing person appeal mentions QuickBooks records',
    'Safeguarding investigation at an accounting software supplier',
    'Serious health incident follows cloud accounting event',
  ])('sensitive context overrides a positive keyword: %s', (title) => {
    expect(selectContextualRecommendation({ ...eligibleArticle, title })).toBeNull();
  });

  test('keeps registry identifiers bounded and stable without Rewarx', () => {
    const recommendation = CONTEXTUAL_RECOMMENDATIONS[0];
    const serialised = JSON.stringify(CONTEXTUAL_RECOMMENDATIONS).toLowerCase();

    expect(isContextualRecommendationRegistryBounded(recommendation)).toBe(true);
    expect(recommendation).toMatchObject({
      card_id: 'accounting_software_guide_v1',
      provider_id: 'cheshire_today_guides',
      placement_id: 'article_after_body',
      destination_type: 'guide',
      variant_version: 'v1',
      disclosure_version: 'affiliate_guide_v1',
    });
    expect(serialised).not.toContain('rewarx');
  });

  test('normalises category without retaining unbounded input', () => {
    expect(normaliseContextualCategory(' Business & Finance ')).toBe('business_finance');
    expect(normaliseContextualCategory('x'.repeat(100))).toHaveLength(32);
  });
});
