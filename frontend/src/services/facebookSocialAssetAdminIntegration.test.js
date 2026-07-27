import fs from 'fs';
import path from 'path';


const source = fs.readFileSync(
  path.join(__dirname, '..', 'components', 'AdminDashboard.jsx'),
  'utf8'
);


test('only eligible Local News rows expose the Facebook graphic dialog action', () => {
  expect(source).toContain("article.category === 'Local News' && article.mongo_id");
  expect(source).toContain('title="Create Facebook Graphic"');
  expect(source).toContain('setFacebookGraphicArticle(article)');
  expect(source).toContain('<FacebookLocalGraphicDialog');
  expect(source).toContain('article={facebookGraphicArticle}');
});


test('the dashboard does not call posting, scheduling or generator transport from the new action', () => {
  expect(source).not.toContain('fetchFacebookLocalGraphic(');
  expect(source).not.toContain('rasterizeFacebookSvg(');
});
