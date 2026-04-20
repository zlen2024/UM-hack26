import Link from 'next/link';
import { ArrowLeft, Shield, Eye, Lock, Database, Mail } from 'lucide-react';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold" style={{ fontFamily: 'serif' }}>K</span>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-700 bg-clip-text text-transparent" style={{ fontFamily: 'serif' }}>
                Kacip CRM
              </span>
            </Link>
            <Link href="/" className="text-gray-600 hover:text-blue-600 transition-colors flex items-center gap-2">
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-2xl shadow-lg p-8 md:p-12">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'serif' }}>Privacy Policy</h1>
            <p className="text-lg text-gray-600">Last Updated: April 20, 2026</p>
          </div>

          <div className="prose prose-lg max-w-none">
            <p className="text-gray-700 leading-relaxed mb-8">
              This Privacy Policy describes how we collect, use, and disclose your information when you use the Kacip CRM application.
            </p>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6 flex items-center gap-3">
              <Eye className="w-6 h-6 text-blue-600" />
              1. Information We Collect
            </h2>

            <h3 className="text-xl font-semibold text-gray-800 mt-8 mb-4">User Account Data</h3>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Email address (login identifier)</li>
              <li>Password (stored as bcrypt hash)</li>
              <li>Full name</li>
              <li>Role</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mt-8 mb-4">Google OAuth Data</h3>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Google email address</li>
              <li>Google access token and refresh token</li>
              <li>Gmail watch expiration and history ID</li>
              <li>Calendar access token and refresh token</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mt-8 mb-4">WhatsApp Business Data</h3>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Phone number ID and display phone number</li>
              <li>WhatsApp access token</li>
              <li>Verify token</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mt-8 mb-4">Contact Information</h3>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Name, email address, phone number</li>
              <li>Company name</li>
              <li>Notes</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mt-8 mb-4">Email Data</h3>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Gmail message ID and thread ID</li>
              <li>Subject, from/to email addresses</li>
              <li>Email snippet (up to 500 characters)</li>
              <li>Full email body (up to 50,000 characters)</li>
              <li>HTML email content</li>
              <li>Label IDs, history ID, read status</li>
              <li>Received timestamp</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mt-8 mb-4">CRM Records</h3>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li><strong>Opportunities:</strong> Title, deal value, stage, contact, assigned user, expected close date</li>
              <li><strong>Tasks:</strong> Title, description, status, priority, due date</li>
              <li><strong>Activities:</strong> Type, description, source, scheduled time</li>
            </ul>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6 flex items-center gap-3">
              <Database className="w-6 h-6 text-green-600" />
              2. How Information is Used
            </h2>
            <p className="text-gray-700 mb-4">We use your information to:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Provide and maintain the CRM services</li>
              <li>Authenticate user accounts</li>
              <li>Integrate with Google Gmail and Calendar</li>
              <li>Enable WhatsApp Business messaging</li>
              <li>Manage customer relationships</li>
              <li>Provide automated support and AI-powered features</li>
              <li>Personalize your experience</li>
            </ul>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6">3. Data Retention</h2>
            <p className="text-gray-700">
              We retain your data for as long as your account is active or as needed to provide services. You may request deletion at any time.
            </p>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6 flex items-center gap-3">
              <Lock className="w-6 h-6 text-red-600" />
              4. Data Deletion
            </h2>
            <p className="text-gray-700 mb-4">
              To request deletion of your data, please contact us at:
            </p>
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="font-semibold text-gray-900">Email: nelz020513@gmail.com</p>
              <p className="text-gray-700 mt-2">Include "Data Deletion Request" in the subject line.</p>
            </div>
            <p className="text-gray-700 mb-4">We will:</p>
            <ol className="list-decimal pl-6 space-y-2 text-gray-700">
              <li>Verify your identity</li>
              <li>Delete your data from our active database within 30 days</li>
            </ol>
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg mt-4">
              <p className="text-yellow-800 font-semibold">Note:</p>
              <p className="text-yellow-700 mt-1">Account deletion requires contacting the developer directly at nelz020513@gmail.com. We do not provide self-service account deletion.</p>
            </div>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6">5. Third-Party Disclosure</h2>
            <p className="text-gray-700 mb-4">We may share your information with third-party service providers:</p>

            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border border-gray-300 rounded-lg">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b">Service</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-b">Purpose</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr>
                    <td className="px-4 py-3 text-sm text-gray-700">Supabase</td>
                    <td className="px-4 py-3 text-sm text-gray-700">Database hosting</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm text-gray-700">Google/Gmail API</td>
                    <td className="px-4 py-3 text-sm text-gray-700">Email integration</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm text-gray-700">Google Calendar API</td>
                    <td className="px-4 py-3 text-sm text-gray-700">Calendar sync</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm text-gray-700">Meta/Facebook WhatsApp API</td>
                    <td className="px-4 py-3 text-sm text-gray-700">WhatsApp Business messaging</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-gray-700 mt-4">
              These providers are contractually obligated to protect your information.
            </p>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6">6. Children's Privacy</h2>
            <p className="text-gray-700">
              Our service is not intended for children under 13. We do not knowingly collect personal information from children under 13.
            </p>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6">7. User Rights</h2>
            <p className="text-gray-700 mb-4">You have the right to:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Access your personal data</li>
              <li>Request correction of inaccurate data</li>
              <li>Request deletion of your data</li>
              <li>Withdraw consent at any time</li>
            </ul>
            <p className="text-gray-700 mt-4">
              To exercise these rights, contact us at nelz020513@gmail.com.
            </p>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6">8. Security</h2>
            <p className="text-gray-700 mb-4">We implement security measures including:</p>
            <ul className="list-disc pl-6 space-y-2 text-gray-700">
              <li>Bcrypt password hashing</li>
              <li>JWT authentication</li>
              <li>HTTPS encryption</li>
            </ul>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-6 flex items-center gap-3">
              <Mail className="w-6 h-6 text-blue-600" />
              9. Contact Information
            </h2>
            <p className="text-gray-700 mb-4">
              For any privacy-related inquiries, contact:
            </p>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="font-semibold text-blue-900">Email: nelz020513@gmail.com</p>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-gray-200 text-center">
            <Link href="/" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-semibold">
              <ArrowLeft className="w-4 h-4" />
              Back to Kacip CRM
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}