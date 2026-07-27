import fs from 'fs';
import path from 'path';


const source = fs.readFileSync(
  path.join(__dirname, '..', 'components', 'AdminDashboard.jsx'),
  'utf8'
);


test('article rows with canonical Mongo IDs expose the shared Social Publishing action', () => {
  expect(source).toContain('{article.mongo_id && (');
  expect(source).not.toContain("article.category === 'Local News' && article.mongo_id");
  expect(source).toContain('title="Social Publishing"');
  expect(source).toContain('setSocialPublishingArticle(article)');
  expect(source).toContain('<SocialPublishingDialog');
  expect(source).toContain('article={socialPublishingArticle}');
});


test('the dashboard does not call posting, scheduling or generator transport from the new action', () => {
  expect(source).not.toContain('fetchFacebookLocalGraphic(');
  expect(source).not.toContain('rasterizeFacebookSvg(');
});
