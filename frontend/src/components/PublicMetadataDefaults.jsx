import React from "react";
import { Helmet } from "react-helmet-async";
import { useLocation } from "react-router-dom";

const PUBLIC_SITE_URL = "https://cheshiretoday.co.uk";
const DEFAULT_PUBLIC_DESCRIPTION =
  "Latest local, business, finance, AI and UK news from Cheshire Today.";

export default function PublicMetadataDefaults() {
  const { pathname } = useLocation();
  if (pathname !== "/") return null;

  return (
    <Helmet defer={false}>
      <meta name="description" content={DEFAULT_PUBLIC_DESCRIPTION} />
      <link rel="canonical" href={`${PUBLIC_SITE_URL}/`} />
      <meta property="og:url" content={`${PUBLIC_SITE_URL}/`} />
    </Helmet>
  );
}
