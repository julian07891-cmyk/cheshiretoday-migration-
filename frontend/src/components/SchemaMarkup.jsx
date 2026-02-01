import React from 'react';
import { Helmet } from 'react-helmet-async';

const SchemaMarkup = ({ article, type = 'NewsArticle' }) => {
  if (!article) return null;

  const schema = {
    '@context': 'https://schema.org',
    '@type': type,
    'headline': article.title,
    'description': article.content?.substring(0, 200),
    'image': article.image,
    'datePublished': article.publishedDate || article.created_at,
    'dateModified': article.publishedDate || article.created_at,
    'author': {
      '@type': 'Organization',
      'name': 'Cheshire Today',
      'url': 'https://cheshiretoday.co.uk'
    },
    'publisher': {
      '@type': 'Organization',
      'name': 'Cheshire Today',
      'logo': {
        '@type': 'ImageObject',
        'url': 'https://cheshiretoday.co.uk/logo.png'
      }
    },
    'mainEntityOfPage': {
      '@type': 'WebPage',
      '@id': `https://cheshiretoday.co.uk/article/${article.id}`
    }
  };

  // Add location for Local News
  if (article.category === 'Local News') {
    schema.contentLocation = {
      '@type': 'Place',
      'name': 'Cheshire, United Kingdom',
      'address': {
        '@type': 'PostalAddress',
        'addressRegion': 'Cheshire',
        'addressCountry': 'GB'
      }
    };
  }

  return (
    <Helmet>
      <script type="application/ld+json">
        {JSON.stringify(schema)}
      </script>
    </Helmet>
  );
};

export default SchemaMarkup;
