// components/Chat/ChatInterface.js
import React, { useState, useRef, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';
import ChatBubble from './ChatBubble';
import ChatInput from './ChatInput';
import Loading from '../common/Loading';
import CampaignPreview from '../Campaign/CampaignPreview';
import CampaignForm from '../Campaign/CampaignForms';
import AnalyticsDashboard from '../analytics/AnalyticsDashboard';
import AdminTemplates from '../admin/AdminTemplates';
import { sendStreamingMessage, createCampaign } from '../../services/chat';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [campaignData, setCampaignData] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [sidebarTab, setSidebarTab] = useState('draft'); // 'draft' | 'analytics' | 'templates'
  const [darkMode, setDarkMode] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    setMessages(prev => [
      ...prev, 
      { type: 'user', content: text },
      { type: 'assistant', content: '', isStreaming: true }
    ]);
    setLoading(true);

    let currentResponseText = '';

    try {
      await sendStreamingMessage(
        text,
        (token) => {
          currentResponseText += token;
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.type === 'assistant') {
              last.content = currentResponseText;
            }
            return updated;
          });
        },
        (businessInfo) => {
          console.log('Business info extracted:', businessInfo);
        },
        (data) => {
          setCampaignData(data);
          setSidebarTab('draft'); // Automatically open draft when generated
        }
      );

      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last && last.type === 'assistant') {
          delete last.isStreaming;
        }
        return updated;
      });
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => {
        const filtered = prev.filter(m => !(m.type === 'assistant' && m.content === ''));
        return [...filtered, { 
          type: 'error', 
          content: 'Sorry, there was an error processing your message.' 
        }];
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCampaign = async () => {
    setLoading(true);
    try {
      const payload = {
        headlines: campaignData.headlines || [],
        descriptions: campaignData.descriptions || [campaignData.description],
        keywords: campaignData.keywords || [],
        daily_budget: Number(campaignData.daily_budget || 10)
      };
      const response = await createCampaign(payload);
      alert(`Campaign created successfully! ID: ${response.campaign_id}`);
    } catch (error) {
      console.error('Error creating campaign:', error);
      alert(`Failed to create campaign: ${error.message || error}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCampaign = (updatedData) => {
    setCampaignData(updatedData);
    setIsEditing(false);
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-200">
      <div className="flex-1 flex flex-col max-h-screen">
        {/* Top Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 transition-colors duration-200">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
            <h1 className="text-base font-bold text-slate-800 dark:text-slate-100">AI Ads Copilot</h1>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 chat-container space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-slate-400 mt-10">
              <h2 className="text-xl font-bold text-slate-700 dark:text-slate-300 mb-2">Welcome to AI Ad Assistant</h2>
              <p className="text-sm dark:text-slate-400">Describe your business, location, and budget to get started.</p>
            </div>
          )}
          {messages.map((message, index) => (
            <ChatBubble key={index} {...message} />
          ))}
          {loading && <Loading />}
          <div ref={messagesEndRef} />
        </div>
        <ChatInput onSend={handleSendMessage} disabled={loading} />
      </div>

      {/* Sidebar Panel */}
      <div className="w-[450px] border-l border-slate-200 dark:border-slate-800 h-screen flex flex-col bg-white dark:bg-slate-950 transition-colors duration-200">
        {/* Sidebar Tabs */}
        <div className="flex border-b border-slate-100 dark:border-slate-800">
          <button
            onClick={() => setSidebarTab('draft')}
            className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider text-center border-b-2 transition-colors ${
              sidebarTab === 'draft'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-slate-50/50 dark:bg-slate-900/50'
                : 'border-transparent text-slate-400 dark:text-slate-500 hover:text-slate-600'
            }`}
          >
            Campaign Draft
          </button>
          <button
            onClick={() => setSidebarTab('analytics')}
            className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider text-center border-b-2 transition-colors ${
              sidebarTab === 'analytics'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-slate-50/50 dark:bg-slate-900/50'
                : 'border-transparent text-slate-400 dark:text-slate-500 hover:text-slate-600'
            }`}
          >
            Analytics
          </button>
          <button
            onClick={() => setSidebarTab('templates')}
            className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider text-center border-b-2 transition-colors ${
              sidebarTab === 'templates'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-slate-50/50 dark:bg-slate-900/50'
                : 'border-transparent text-slate-400 dark:text-slate-500 hover:text-slate-600'
            }`}
          >
            Templates Admin
          </button>
        </div>

        {/* Sidebar Content */}
        <div className="flex-1 overflow-y-auto">
          {sidebarTab === 'draft' && (
            campaignData ? (
              isEditing ? (
                <CampaignForm
                  data={campaignData}
                  onSave={handleSaveCampaign}
                  onCancel={() => setIsEditing(false)}
                />
              ) : (
                <CampaignPreview
                  data={campaignData}
                  onEdit={() => setIsEditing(true)}
                  onCreate={handleCreateCampaign}
                />
              )
            ) : (
              <div className="p-8 text-center text-slate-400 dark:text-slate-500 mt-20">
                <p className="text-sm">No campaign draft active yet.</p>
                <p className="text-xs mt-1">Chat with the assistant to extract details and generate a campaign.</p>
              </div>
            )
          )}
          {sidebarTab === 'analytics' && <AnalyticsDashboard />}
          {sidebarTab === 'templates' && <AdminTemplates />}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;