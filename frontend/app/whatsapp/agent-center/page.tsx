'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import { MessageCircle, Send, User, Bot, ArrowLeft, Phone, MoreVertical, Sparkles, Lightbulb, Calendar, FileText, CheckCircle } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'agent';
  content: string;
  timestamp: string;
  type: 'text' | 'system';
}

const mockMessages: Message[] = [
  {
    id: '1',
    sender: 'user',
    content: 'Hi, I\'m interested in your services. Can you tell me more about your pricing?',
    timestamp: '10:30 AM',
    type: 'text'
  },
  {
    id: '2',
    sender: 'agent',
    content: 'Hello! Thank you for your interest. Our pricing starts at $99/month for the basic plan. Would you like me to send you a detailed brochure?',
    timestamp: '10:32 AM',
    type: 'text'
  },
  {
    id: '3',
    sender: 'user',
    content: 'Yes, please send the brochure. Also, do you offer a free trial?',
    timestamp: '10:35 AM',
    type: 'text'
  },
  {
    id: '4',
    sender: 'agent',
    content: 'Great! I\'ve sent the brochure to your email. Yes, we offer a 14-day free trial with full access to all features. Would you like to start the trial now?',
    timestamp: '10:37 AM',
    type: 'text'
  },
  {
    id: '5',
    sender: 'user',
    content: 'That sounds perfect. Let\'s start the trial.',
    timestamp: '10:40 AM',
    type: 'text'
  },
  {
    id: '6',
    sender: 'agent',
    content: 'Excellent! I\'ve activated your 14-day free trial. You should receive a confirmation email shortly with your login details. Is there anything else I can help you with today?',
    timestamp: '10:42 AM',
    type: 'text'
  }
];

const mockConversations = [
  { id: '1', name: 'John Doe', lastMessage: 'That sounds perfect. Let\'s start the trial.', time: '10:42 AM', unread: 0 },
  { id: '2', name: 'Jane Smith', lastMessage: 'When will the product be available?', time: '9:15 AM', unread: 2 },
  { id: '3', name: 'Bob Johnson', lastMessage: 'Thank you for the information.', time: 'Yesterday', unread: 0 },
  { id: '4', name: 'Alice Brown', lastMessage: 'Can I schedule a demo?', time: 'Yesterday', unread: 1 },
];

export default function WhatsAppAgentCenter() {
  const router = useRouter();
  const [selectedConversation, setSelectedConversation] = useState('1');
  const [newMessage, setNewMessage] = useState('');

  const currentMessages = mockMessages.filter(msg => msg.id); // All messages for now

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      // In a real app, this would send the message
      console.log('Sending message:', newMessage);
      setNewMessage('');
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b px-6 py-4 flex items-center gap-4">
          <button
            onClick={() => router.push('/whatsapp')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">WhatsApp Agent Center</h1>
              <p className="text-sm text-gray-500">Mockup - Manage customer conversations</p>
            </div>
          </div>
        </div>

        <div className="flex-1 flex">
          {/* Conversations List */}
          <div className="w-80 bg-white border-r flex flex-col">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-gray-900">Conversations</h2>
            </div>
            <div className="flex-1 overflow-y-auto">
              {mockConversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConversation(conv.id)}
                  className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                    selectedConversation === conv.id ? 'bg-green-50 border-l-4 border-l-green-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium truncate">{conv.name}</p>
                        {conv.unread > 0 && (
                          <span className="bg-green-500 text-white text-xs rounded-full px-2 py-0.5">
                            {conv.unread}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 truncate">{conv.lastMessage}</p>
                    </div>
                    <p className="text-xs text-gray-400">{conv.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Chat Area */}
          <div className="flex-1 flex flex-col">
            {/* Chat Header */}
            <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-gray-600" />
                </div>
                <div>
                  <p className="font-medium">John Doe</p>
                  <p className="text-sm text-gray-500">+1 (555) 123-4567</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 hover:bg-gray-100 rounded-lg">
                  <Phone className="w-5 h-5" />
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg">
                  <MoreVertical className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="flex-1 flex">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {currentMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.sender === 'user'
                          ? 'bg-green-500 text-white'
                          : 'bg-white border'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      <p className={`text-xs mt-1 ${
                        message.sender === 'user' ? 'text-green-100' : 'text-gray-500'
                      }`}>
                        {message.timestamp}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* AI Suggestions Panel */}
              <div className="w-80 bg-gradient-to-b from-blue-50 to-indigo-50 border-l border-blue-200 flex flex-col">
                <div className="p-4 border-b border-blue-200 bg-white/80 backdrop-blur-sm">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-blue-600" />
                    <h3 className="font-semibold text-gray-900">AI Suggestions</h3>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">Smart recommendations for next steps</p>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  <div className="bg-white rounded-lg p-3 border border-blue-200 shadow-sm">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <Calendar className="w-4 h-4 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">Schedule Follow-up Call</p>
                        <p className="text-xs text-gray-600 mt-1">Customer expressed interest in trial. Suggest booking a demo call to discuss features.</p>
                        <button className="mt-2 text-xs bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 transition-colors">
                          Schedule Call
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-3 border border-green-200 shadow-sm">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <FileText className="w-4 h-4 text-green-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">Send Product Documentation</p>
                        <p className="text-xs text-gray-600 mt-1">Share detailed feature list and integration guide to help with evaluation.</p>
                        <button className="mt-2 text-xs bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700 transition-colors">
                          Send Docs
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-3 border border-purple-200 shadow-sm">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <CheckCircle className="w-4 h-4 text-purple-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">Create Sales Opportunity</p>
                        <p className="text-xs text-gray-600 mt-1">High-value lead showing purchase intent. Add to opportunities pipeline.</p>
                        <button className="mt-2 text-xs bg-purple-600 text-white px-3 py-1 rounded-md hover:bg-purple-700 transition-colors">
                          Add to Pipeline
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-3 border border-orange-200 shadow-sm">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <Lightbulb className="w-4 h-4 text-orange-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">Offer Limited-Time Discount</p>
                        <p className="text-xs text-gray-600 mt-1">Customer mentioned budget concerns. Consider 10% discount for first 3 months.</p>
                        <button className="mt-2 text-xs bg-orange-600 text-white px-3 py-1 rounded-md hover:bg-orange-700 transition-colors">
                          Apply Discount
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-4 border-t border-blue-200 bg-white/60">
                  <p className="text-xs text-gray-500 text-center">
                    AI suggestions are generated based on conversation context
                  </p>
                </div>
              </div>
            </div>

            {/* Message Input */}
            <div className="bg-white border-t p-4">
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Type a message..."
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={!newMessage.trim()}
                  className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2 text-center">
                This is a mockup. Real WhatsApp integration coming soon.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}