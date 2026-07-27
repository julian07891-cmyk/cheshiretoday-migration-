import React from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { BriefcaseBusiness, Building2, Check, Cpu, Mail, Newspaper } from "lucide-react";
import NewsletterFull from "../components/homepage/NewsletterFull";
import NewsFooter from "../components/NewsFooter";


const PAGE_URL = "https://cheshiretoday.co.uk/newsletter";
const PAGE_TITLE = "Cheshire Today Newsletter | Local News and Business Briefing";
const PAGE_DESCRIPTION = "Subscribe free to the Cheshire Today newsletter for local news, business, property, finance and AI & Tech updates from across Cheshire.";
const OG_TITLE = "Stay ahead with Cheshire’s daily briefing";
const OG_DESCRIPTION = "Local news, business, property, finance and AI & Tech stories delivered free to your inbox.";
const OG_IMAGE = "https://cheshiretoday.co.uk/cheshire-today-newsletter-share.png";

const benefits = [
  [Newspaper, "Cheshire Daily Brief"],
  [Building2, "Major local developments"],
  [BriefcaseBusiness, "Business and investment updates"],
  [Building2, "Property and housing news"],
  [Cpu, "AI & Tech coverage"],
  [Mail, "Weekly roundup"],
];

const faqs = [
  ["Is it free?", "Yes. The Cheshire Today newsletter is free to subscribe to."],
  ["How often will I receive it?", "The Daily Brief is sent Monday to Saturday. The Weekly Roundup is sent on Sunday."],
  ["Can I unsubscribe?", "Yes. Every newsletter includes a secure unsubscribe option."],
  ["What topics are covered?", "Local news, business, investment, property, housing, finance and AI & Tech from across Cheshire."],
];

export default function NewsletterPage() {
  const focusSignup = () => {
    const field = document.getElementById("newsletter-signup-email");
    field?.scrollIntoView?.({ behavior: "smooth", block: "center" });
    field?.focus({ preventScroll: true });
  };

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-[#F7F4EE] text-[#1E293B]">
      <Helmet>
        <title>{PAGE_TITLE}</title>
        <meta name="description" content={PAGE_DESCRIPTION} />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href={PAGE_URL} />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={PAGE_URL} />
        <meta property="og:title" content={OG_TITLE} />
        <meta property="og:description" content={OG_DESCRIPTION} />
        <meta property="og:image" content={OG_IMAGE} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={OG_TITLE} />
        <meta name="twitter:description" content={OG_DESCRIPTION} />
        <meta name="twitter:image" content={OG_IMAGE} />
      </Helmet>

      <header className="border-b border-[#E6E1D8] bg-[#FBFAF7]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <Link to="/" className="font-serif text-2xl font-bold text-[#020617] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A]">
            Cheshire Today
          </Link>
          <Link to="/" className="text-sm font-semibold text-[#1E3A8A] underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A]">
            Back to news
          </Link>
        </div>
      </header>

      <main className="w-full">
        <section className="bg-[#1E3A8A] px-4 py-16 text-center text-[#F7F4EE] sm:px-6 sm:py-24">
          <div className="mx-auto max-w-4xl">
            <p className="mb-4 font-sans text-sm font-bold uppercase tracking-[0.18em] text-emerald-200">The Cheshire Today newsletter</p>
            <h1 className="font-serif text-4xl font-bold leading-tight sm:text-5xl lg:text-6xl">Stay ahead with Cheshire’s daily briefing</h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-blue-50">Local news, business, property, finance and AI & Tech stories delivered free to your inbox.</p>
            <button type="button" onClick={focusSignup} className="mt-8 rounded-full bg-[#F7F4EE] px-7 py-3 font-sans font-bold text-[#1E3A8A] hover:bg-white focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-emerald-300">
              Subscribe free
            </button>
          </div>
        </section>

        <section aria-labelledby="newsletter-benefits" className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
          <h2 id="newsletter-benefits" className="text-center font-serif text-3xl font-bold text-[#020617]">What you’ll receive</h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {benefits.map(([Icon, label]) => (
              <div key={label} className="flex items-center gap-3 rounded-xl border border-[#E6E1D8] bg-[#FBFAF7] p-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-[#047857]"><Icon aria-hidden="true" className="h-5 w-5" /></span>
                <span className="font-semibold text-[#1E293B]">{label}</span>
              </div>
            ))}
          </div>
        </section>

        <section aria-labelledby="newsletter-signup-heading" className="mx-auto max-w-4xl px-4 pb-14 sm:px-6">
          <h2 id="newsletter-signup-heading" className="mb-6 text-center font-serif text-3xl font-bold text-[#020617]">Subscribe free</h2>
          <NewsletterFull />
        </section>

        <section aria-labelledby="newsletter-trust" className="border-y border-[#E6E1D8] bg-[#FBFAF7] px-4 py-12 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <Check aria-hidden="true" className="mx-auto h-8 w-8 text-[#047857]" />
            <h2 id="newsletter-trust" className="mt-3 font-serif text-2xl font-bold text-[#020617]">Free, straightforward and privacy-respecting</h2>
            <p className="mt-3 leading-7 text-[#475569]">Subscribe free and unsubscribe at any time. We use your details to manage your requested newsletters and preferences. Read our <Link to="/privacy" className="font-semibold text-[#1E3A8A] underline">Privacy Policy</Link>.</p>
          </div>
        </section>

        <section aria-labelledby="newsletter-faq" className="mx-auto max-w-4xl px-4 py-14 sm:px-6">
          <h2 id="newsletter-faq" className="font-serif text-3xl font-bold text-[#020617]">Newsletter FAQ</h2>
          <div className="mt-6 space-y-4">
            {faqs.map(([question, answer]) => (
              <article key={question} className="rounded-xl border border-[#E6E1D8] bg-[#FBFAF7] p-5">
                <h3 className="font-serif text-xl font-bold text-[#020617]">{question}</h3>
                <p className="mt-2 leading-7 text-[#475569]">{answer}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      <NewsFooter />
    </div>
  );
}
