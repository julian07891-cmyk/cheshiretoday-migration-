import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText } from 'lucide-react';

const TermsOfService = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-emerald-700 text-white py-8">
        <div className="container mx-auto px-4">
          <Link to="/" className="inline-flex items-center text-emerald-100 hover:text-white mb-4 transition-colors">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Home
          </Link>
          <div className="flex items-center gap-3">
            <FileText className="h-10 w-10" />
            <h1 className="text-3xl md:text-4xl font-bold">Terms of Service</h1>
          </div>
          <p className="mt-2 text-emerald-100">Last updated: January {currentYear}</p>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 md:p-12">
          
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Agreement to Terms</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              By accessing and using Cheshire Today (cheshiretoday.co.uk), you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our website.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Description of Service</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              Cheshire Today is a digital publication covering Cheshire local news, business, finance, AI & technology and selected UK developments. Our content may include original reporting, curated summaries, RSS-sourced coverage and AI-assisted editorial workflows, alongside links to relevant third-party sources where appropriate.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Content and Copyright</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
              Content published on Cheshire Today may consist of:
            </p>
            <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-2 ml-4">
              <li>Original Cheshire Today reporting, analysis and explainers</li>
              <li>Headlines and summaries sourced or adapted from publicly available feeds and third-party reporting</li>
              <li>Links to original articles on third-party websites</li>
              <li>Images provided by the original publishers</li>
            </ul>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed mt-4">
              Original Cheshire Today content belongs to Cheshire Today. Third-party source material, images, trademarks and publisher content remain the property of their respective owners. Where relevant, we encourage readers to visit original sources for full reporting.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">User Conduct</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
              When using our website, you agree not to:
            </p>
            <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-2 ml-4">
              <li>Use the website for any unlawful purpose</li>
              <li>Attempt to gain unauthorised access to any part of the website</li>
              <li>Interfere with or disrupt the website's operation</li>
              <li>Use automated systems to access the website without permission</li>
              <li>Reproduce or redistribute our content without permission</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Newsletter Subscription</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              By subscribing to our newsletter, you consent to receive periodic email updates containing news headlines and links. You may unsubscribe at any time by clicking the unsubscribe link in any email or by contacting us directly.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Advertising</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              Cheshire Today may feature sponsored placements, commercial partnerships and affiliate links. Where readers click eligible affiliate links and complete a purchase, Cheshire Today may earn a commission at no extra cost to the reader. Commercial content and monetised links may appear across editorial, guide and product-related pages. For more information, please visit <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer" className="text-emerald-600 hover:underline">our Affiliate Disclosure and Privacy Policy</a>.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Disclaimer</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
              While we strive to provide accurate and up-to-date news content:
            </p>
            <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-2 ml-4">
              <li>We do not guarantee the accuracy, completeness, or timeliness of any content</li>
              <li>News content is sourced from third-party publishers and we are not responsible for their content</li>
              <li>The website is provided "as is" without warranties of any kind</li>
              <li>We are not liable for any damages arising from the use of this website</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">External Links</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              Our website contains links to external websites. We are not responsible for the content, privacy practices, or terms of service of these external sites. We encourage you to review the terms and privacy policies of any external websites you visit.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Limitation of Liability</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              To the fullest extent permitted by law, Cheshire Today shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the website.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Changes to Terms</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              We reserve the right to modify these Terms of Service at any time. Changes will be effective immediately upon posting. Your continued use of the website after any changes constitutes acceptance of the new terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Governing Law</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              These Terms of Service shall be governed by and construed in accordance with the laws of England and Wales. Any disputes arising from these terms shall be subject to the exclusive jurisdiction of the courts of England and Wales.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Contact Us</h2>
            <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
              If you have any questions about these Terms of Service, please contact us at:
            </p>
            <p className="text-gray-700 dark:text-gray-300 mt-2">
              <strong>Email:</strong> <a href="mailto:news@cheshiretoday.co.uk" className="text-emerald-600 hover:underline">news@cheshiretoday.co.uk</a>
            </p>
          </section>

        </div>
      </div>

      {/* Simple Footer */}
      <div className="bg-gray-900 text-gray-400 py-6">
        <div className="container mx-auto px-4 text-center">
          <p>© {currentYear} Cheshire Today. All rights reserved.</p>
          <div className="mt-2 space-x-4">
            <Link to="/" className="hover:text-emerald-400 transition-colors">Home</Link>
            <span>|</span>
            <Link to="/privacy" className="hover:text-emerald-400 transition-colors">Privacy Policy</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TermsOfService;
