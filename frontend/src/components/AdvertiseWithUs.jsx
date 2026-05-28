import React from 'react';
import { Mail, Users, TrendingUp, Award } from 'lucide-react';

const AdvertiseWithUs = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Advertise With Cheshire Today
          </h1>
          <p className="text-xl text-gray-600">
            Reach thousands of engaged readers in Cheshire and across the UK
          </p>
        </div>

        {/* Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <Users className="w-12 h-12 text-green-600 mx-auto mb-3" />
            <h3 className="text-3xl font-bold text-gray-900">Growing</h3>
            <p className="text-gray-600">Monthly Visitors</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <TrendingUp className="w-12 h-12 text-green-600 mx-auto mb-3" />
            <h3 className="text-3xl font-bold text-gray-900">Daily</h3>
            <p className="text-gray-600">Morning Brief newsletter</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <Award className="w-12 h-12 text-green-600 mx-auto mb-3" />
            <h3 className="text-3xl font-bold text-gray-900">Local Focus</h3>
            <p className="text-gray-600">Cheshire Community</p>
          </div>
        </div>

        {/* Advertising Options */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Advertising Options</h2>
          
          <div className="space-y-6">
            {/* Banner Ads */}
            <div className="border-b pb-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Display Banner Ads</h3>
              <p className="text-gray-600 mb-3">
                Premium placement on our homepage and article pages
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Header Banner (728×90) - Prime visibility</li>
                <li>Sidebar Placement (300×600) - Persistent presence</li>
                <li>Between Articles (300×250) - High engagement</li>
              </ul>
              <p className="text-green-600 font-semibold mt-3">From £100/month</p>
            </div>

            {/* Sponsored Content */}
            <div className="border-b pb-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Sponsored Articles</h3>
              <p className="text-gray-600 mb-3">
                Native content that engages readers while promoting your brand
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Professional content creation included</li>
                <li>Featured placement on homepage</li>
                <li>Social media promotion</li>
                <li>Permanent archive presence</li>
              </ul>
              <p className="text-green-600 font-semibold mt-3">From £150/article</p>
            </div>

            {/* Newsletter Sponsorship */}
            <div className="border-b pb-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Newsletter Sponsorship</h3>
              <p className="text-gray-600 mb-3">
                Reach subscribers directly in their inbox
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Top placement in daily/weekly digest</li>
                <li>Direct link to your website</li>
                <li>Exclusive messaging to engaged audience</li>
              </ul>
              <p className="text-green-600 font-semibold mt-3">From £75/newsletter</p>
            </div>

            {/* Custom Packages */}
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Custom Packages</h3>
              <p className="text-gray-600 mb-3">
                Tailored solutions for your specific marketing goals
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li>Multi-month discount packages</li>
                <li>Event coverage and promotion</li>
                <li>Video content integration</li>
                <li>Social media campaigns</li>
              </ul>
              <p className="text-green-600 font-semibold mt-3">Contact for pricing</p>
            </div>
          </div>
        </div>

        {/* Why Advertise Section */}
        <div className="bg-green-50 rounded-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Why Advertise With Us?</h2>
          <ul className="space-y-3 text-gray-700">
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span><strong>Local Audience:</strong> Targeted reach to Cheshire residents and businesses</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span><strong>Engaged Readers:</strong> Quality content drives high engagement rates</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span><strong>Fresh Content:</strong> Daily news updates and breaking alerts keep readers engaged</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span><strong>Multiple Channels:</strong> Website, social media, and newsletter reach</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span><strong>Flexible Options:</strong> Packages to suit any budget and goal</span>
            </li>
          </ul>
        </div>

        {/* Contact Section */}
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <Mail className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Get Started Today</h2>
          <p className="text-gray-600 mb-6">
            Contact us to discuss your advertising needs and get a custom quote
          </p>
          <a
            href="mailto:advertising@cheshiretoday.co.uk"
            className="inline-block bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
          >
            Contact Us
          </a>
          <p className="text-gray-500 mt-4">
            Email: advertising@cheshiretoday.co.uk
          </p>
        </div>

        {/* Testimonial Placeholder */}
        <div className="mt-8 bg-gray-100 rounded-lg p-6 text-center">
          <p className="text-gray-600 italic">
            "Advertising with Cheshire Today helped us reach exactly the local audience we needed. 
            Highly recommended for any Cheshire-based business!"
          </p>
          <p className="text-gray-800 font-semibold mt-3">- Local Business Owner</p>
        </div>
      </div>
    </div>
  );
};

export default AdvertiseWithUs;
