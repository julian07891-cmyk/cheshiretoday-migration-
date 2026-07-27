import fs from 'fs';
import path from 'path';


const source = fs.readFileSync(
  path.join(__dirname, '..', 'components', 'AdminDashboard.jsx'),
  'utf8'
);


test('article rows with canonical Mongo IDs expose the multi-type Facebook graphic action', () => {
  expect(source).toContain('{article.mongo_id && (');
  expect(source).not.toContain("article.category === 'Local News' && article.mongo_id");
  expect(source).toContain('title="Create Facebook Graphic"');
  expect(source).toContain('setFacebookGraphicArticle(article)');
  expect(source).toContain('<FacebookLocalGraphicDialog');
  expect(source).toContain('article={facebookGraphicArticle}');
});


test('the dashboard does not call posting, scheduling or generator transport from the new action', () => {
  expect(source).not.toContain('fetchFacebookLocalGraphic(');
  expect(source).not.toContain('rasterizeFacebookSvg(');
});
