import React from "react";
import { Helmet } from "react-helmet-async";
import { useLocation } from "react-router-dom";

const PUBLIC_SITE_URL = "https://cheshiretoday.co.uk";
const DEFAULT_PUBLIC_DESCRIPTION =
  "Latest local, business, finance, AI and UK news from Cheshire Today.";
const DEFAULT_SOCIAL_IMAGE = `${PUBLIC_SITE_URL}/social-share.jpg`;

export default function PublicMetadataDefaults() {
  const { pathname } = useLocation();

  return (
    <Helmet defer={false}>
      {pathname === "/" && (
        <>
          <meta name="description" content={DEFAULT_PUBLIC_DESCRIPTION} />
          <link rel="canonical" href={`${PUBLIC_SITE_URL}/`} />
          <meta property="og:url" content={`${PUBLIC_SITE_URL}/`} />
          <meta property="og:type" content="website" />
          <meta property="og:image" content={DEFAULT_SOCIAL_IMAGE} />
          <meta property="og:image:secure_url" content={DEFAULT_SOCIAL_IMAGE} />
          <meta property="og:image:type" content="image/jpeg" />
          <meta property="og:image:width" content="1200" />
          <meta property="og:image:height" content="630" />
          <meta property="og:image:alt" content="Cheshire Today News" />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:image" content={DEFAULT_SOCIAL_IMAGE} />
          <meta name="twitter:image:alt" content="Cheshire Today News" />
        </>
      )}
    </Helmet>
  );
}
