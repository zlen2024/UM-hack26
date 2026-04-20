import Link from 'next/link';
import { ArrowRight, CheckCircle, MessageCircle, BarChart3, Users, Calendar, Mail, Bot, Shield, Zap, Star, ChevronDown } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-white/20 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg" style={{ fontFamily: 'serif' }}>K</span>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-700 bg-clip-text text-transparent" style={{ fontFamily: 'serif' }}>
                Kacip CRM
              </span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-600 hover:text-blue-600 transition-colors">Features</a>
              <a href="#agent-centre" className="text-gray-600 hover:text-blue-600 transition-colors">Agent Centre</a>
              <a href="#pricing" className="text-gray-600 hover:text-blue-600 transition-colors">Pricing</a>
              <a href="#privacy" className="text-gray-600 hover:text-blue-600 transition-colors">Privacy</a>
              <Link href="/login" className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-6 py-2 rounded-lg hover:from-blue-700 hover:to-indigo-800 transition-all duration-200 shadow-lg">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-blue-100 px-4 py-2 text-sm text-blue-700 mb-8">
            <Star className="w-4 h-4" />
            Professional CRM for Modern Businesses
          </div>
          <h1 className="text-5xl md:text-7xl font-bold mb-6" style={{ fontFamily: 'serif' }}>
            <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Kacip CRM
            </span>
            <br />
            <span className="text-gray-900">Smarter Customer</span>
            <br />
            <span className="text-gray-700">Relationships</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed">
            Transform your customer interactions with AI-powered insights, automated workflows, and seamless communication across all channels.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/login" className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-8 py-4 rounded-xl hover:from-blue-700 hover:to-indigo-800 transition-all duration-200 shadow-xl text-lg font-semibold flex items-center gap-2">
              Start Free Trial
              <ArrowRight className="w-5 h-5" />
            </Link>
            <button className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-xl hover:border-blue-500 hover:text-blue-600 transition-all duration-200 text-lg font-semibold">
              Watch Demo
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'serif' }}>Powerful Features</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to manage customer relationships effectively
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-200">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                <MessageCircle className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Multi-Channel Communication</h3>
              <p className="text-gray-600">Connect with customers via email, WhatsApp, and more. Never miss an important message.</p>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-200">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-6">
                <Bot className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">AI-Powered Agent Centre</h3>
              <p className="text-gray-600">Intelligent suggestions and automated responses to handle customer inquiries efficiently.</p>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-200">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Advanced Analytics</h3>
              <p className="text-gray-600">Track performance, monitor trends, and make data-driven decisions for your business.</p>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-200">
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-6">
                <Users className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Contact Management</h3>
              <p className="text-gray-600">Organize and manage all your customer information in one centralized location.</p>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-200">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mb-6">
                <Calendar className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Smart Scheduling</h3>
              <p className="text-gray-600">Automate follow-ups, schedule meetings, and never miss important deadlines.</p>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-white/20 hover:shadow-xl transition-all duration-200">
              <div className="w-12 h-12 bg-teal-100 rounded-xl flex items-center justify-center mb-6">
                <Mail className="w-6 h-6 text-teal-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Email Integration</h3>
              <p className="text-gray-600">Seamlessly integrate with Gmail to manage all your email communications.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Agent Centre Section */}
      <section id="agent-centre" className="py-20 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold mb-6" style={{ fontFamily: 'serif' }}>AI-Powered Agent Centre</h2>
              <p className="text-xl text-blue-100 mb-8 leading-relaxed">
                Experience the future of customer service with our intelligent agent centre. Get smart suggestions, automated responses, and insights that help you close deals faster.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <span>Contextual AI suggestions for next steps</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <span>Automated response generation</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <span>Multi-channel conversation management</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <span>Real-time sentiment analysis</span>
                </div>
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
              <div className="space-y-4">
                <div className="bg-white/20 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <Bot className="w-5 h-5 text-blue-300" />
                    <span className="font-semibold">AI Suggestion</span>
                  </div>
                  <p className="text-sm text-blue-100">Schedule a follow-up demo call based on customer interest</p>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <MessageCircle className="w-5 h-5 text-green-300" />
                    <span className="font-semibold">Smart Reply</span>
                  </div>
                  <p className="text-sm text-blue-100">Customer asked about pricing. Generate detailed response.</p>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <BarChart3 className="w-5 h-5 text-purple-300" />
                    <span className="font-semibold">Analytics</span>
                  </div>
                  <p className="text-sm text-blue-100">High-value opportunity detected. Add to sales pipeline.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4" style={{ fontFamily: 'serif' }}>Simple, Transparent Pricing</h2>
            <p className="text-xl text-gray-600">Choose the plan that fits your business needs</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-white/20">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Starter</h3>
              <div className="text-4xl font-bold text-blue-600 mb-6">$29<span className="text-lg text-gray-500">/month</span></div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Up to 100 contacts</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Email integration</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Basic reporting</span>
                </li>
              </ul>
              <Link href="/login" className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg hover:bg-gray-200 transition-colors block text-center font-semibold">
                Get Started
              </Link>
            </div>
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-8 shadow-xl text-white relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-yellow-400 text-black px-4 py-1 rounded-full text-sm font-semibold">
                Most Popular
              </div>
              <h3 className="text-2xl font-bold mb-4">Professional</h3>
              <div className="text-4xl font-bold mb-6">$99<span className="text-lg opacity-80">/month</span></div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-300" />
                  <span>Unlimited contacts</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-300" />
                  <span>WhatsApp integration</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-300" />
                  <span>AI Agent Centre</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-300" />
                  <span>Advanced analytics</span>
                </li>
              </ul>
              <Link href="/login" className="w-full bg-white text-blue-600 py-3 rounded-lg hover:bg-gray-100 transition-colors block text-center font-semibold">
                Start Free Trial
              </Link>
            </div>
            <div className="bg-white rounded-2xl p-8 shadow-lg border border-white/20">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Enterprise</h3>
              <div className="text-4xl font-bold text-purple-600 mb-6">Custom</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Everything in Professional</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Custom integrations</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Dedicated support</span>
                </li>
              </ul>
              <button className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition-colors font-semibold">
                Contact Sales
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Privacy Policy Section */}
      <section id="privacy" className="py-20 bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4" style={{ fontFamily: 'serif' }}>Privacy & Security</h2>
            <p className="text-xl text-gray-300">Your data security is our top priority</p>
          </div>
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10">
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-2xl font-semibold mb-4 flex items-center gap-3">
                  <Shield className="w-6 h-6 text-green-400" />
                  Data Protection
                </h3>
                <ul className="space-y-3 text-gray-300">
                  <li>• End-to-end encryption for all communications</li>
                  <li>• Secure data storage with industry-standard practices</li>
                  <li>• Regular security audits and compliance checks</li>
                  <li>• GDPR and privacy regulation compliance</li>
                </ul>
              </div>
              <div>
                <h3 className="text-2xl font-semibold mb-4 flex items-center gap-3">
                  <Zap className="w-6 h-6 text-blue-400" />
                  Your Rights
                </h3>
                <ul className="space-y-3 text-gray-300">
                  <li>• Full access to your personal data</li>
                  <li>• Right to data deletion and portability</li>
                  <li>• Transparent data usage policies</li>
                  <li>• 24/7 support for privacy concerns</li>
                </ul>
              </div>
            </div>
            <div className="mt-8 pt-8 border-t border-white/10">
              <p className="text-sm text-gray-400 text-center">
                For detailed privacy information, please review our complete{' '}
                <a href="/privacy" className="text-blue-400 hover:text-blue-300 underline">
                  Privacy Policy
                </a>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold mb-6" style={{ fontFamily: 'serif' }}>Ready to Transform Your Customer Relationships?</h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of businesses using Kacip CRM to build stronger customer connections and grow their revenue.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/login" className="bg-white text-blue-600 px-8 py-4 rounded-xl hover:bg-gray-100 transition-all duration-200 shadow-xl text-lg font-semibold flex items-center justify-center gap-2">
              Start Your Free Trial
              <ArrowRight className="w-5 h-5" />
            </Link>
            <button className="border-2 border-white text-white px-8 py-4 rounded-xl hover:bg-white/10 transition-all duration-200 text-lg font-semibold">
              Schedule a Demo
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold" style={{ fontFamily: 'serif' }}>K</span>
                </div>
                <span className="text-xl font-bold" style={{ fontFamily: 'serif' }}>Kacip CRM</span>
              </div>
              <p className="text-gray-400">Smarter customer relationships for modern businesses.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#agent-centre" className="hover:text-white transition-colors">Agent Centre</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="/login" className="hover:text-white transition-colors">Login</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#about" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#careers" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#contact" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="/privacy" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="/terms" className="hover:text-white transition-colors">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
            <p>&copy; 2026 Kacip CRM. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}