import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, ShoppingBag, Info, ExternalLink } from 'lucide-react';

const AffiliateDisclosure = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-[#1E3A8A] text-white py-8">
        <div className="container mx-auto px-4">
          <Link to="/" className="inline-flex items-center text-blue-100 hover:text-white mb-4 transition-colors">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Link>
          <div className="flex items-center gap-3">
            <ShoppingBag className="h-10 w-10" />
            <h1 className="text-3xl md:text-4xl font-bold">Affiliate Disclosure</h1>
          </div>
          <p className="mt-2 text-blue-100">Last updated: January 2026</p>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 md:p-12">
          
          {/* Summary Box */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-8">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <p className="text-blue-800 dark:text-blue-200">
                <strong>In short:</strong> Some links on our site are affiliate links. If you click and make a purchase, we may earn a small commission at no extra cost to you. This helps us keep providing free, quality local news.
              </p>
            </div>
          </div>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">What are affiliate links?</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
              Affiliate links are special URLs that track when you click through from our website to a retailer&apos;s site. If you make a purchase after clicking one of these links, the retailer pays us a small commission. This commission comes from the retailer&apos;s marketing budget – it doesn&apos;t add anything to the price you pay.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Our Affiliate Partners</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed mb-4">
              We work with several trusted affiliate networks and retailers:
            </p>
            <ul className="space-y-3 text-gray-600 dark:text-gray-300">
              <li className="flex items-start gap-2">
                <ExternalLink className="h-5 w-5 text-[#1E3A8A] mt-0.5 flex-shrink-0" />
                <span><strong>Amazon Associates</strong> – As an Amazon Associate, we earn from qualifying purchases made through links to Amazon.co.uk</span>
              </li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">How we choose what to recommend</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed mb-4">
              Our editorial team selects products based on:
            </p>
            <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
              <li>Relevance to our readers in Cheshire and the UK</li>
              <li>Quality and value for money</li>
              <li>Customer reviews and ratings</li>
              <li>Our own research and, where possible, hands-on testing</li>
            </ul>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
              We never recommend products solely because they offer higher commissions. Our readers&apos; trust is more valuable than any affiliate payment.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">How to identify affiliate links</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed mb-4">
              We mark affiliate content clearly. Look for labels such as:
            </p>
            <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
              <li>&ldquo;Ad&rdquo; or &ldquo;Sponsored&rdquo; badges</li>
              <li>&ldquo;Affiliate links&rdquo; text near product recommendations</li>
              <li>&ldquo;We may earn commission from links on this page&rdquo;</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Why we use affiliate links</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed mb-4">
              Running a local news website costs money – from hosting and technology to the time spent researching and writing articles. Affiliate income helps us:
            </p>
            <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
              <li>Keep our news content free for everyone</li>
              <li>Maintain our website and technology</li>
              <li>Invest in better journalism and coverage</li>
              <li>Reduce reliance on intrusive advertising</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Your choices</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed mb-4">
              You&apos;re never obligated to use our affiliate links. If you prefer, you can:
            </p>
            <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2">
              <li>Go directly to the retailer&apos;s website</li>
              <li>Search for the product yourself</li>
              <li>Use an ad blocker (though this may affect some site functionality)</li>
            </ul>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed mt-4">
              We appreciate when you do use our links, as it directly supports our journalism at no cost to you.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Questions?</h2>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
              If you have any questions about our affiliate relationships or how we fund our journalism, please contact us at{' '}
              <a href="mailto:news@cheshiretoday.co.uk" className="text-[#1E3A8A] hover:underline">
                news@cheshiretoday.co.uk
              </a>
            </p>
          </section>

        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="mb-2">© 2026 Cheshire Today. All rights reserved.</p>
          <div className="flex justify-center gap-4">
            <Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-white transition-colors">Terms of Service</Link>
            <Link to="/" className="hover:text-white transition-colors">Home</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AffiliateDisclosure;
