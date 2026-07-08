// components/Chat/ChatInterface.js
import React, { useState, useRef, useEffect } from 'react';
import ChatBubble from '/ChatBubble';
import ChatInput from '/ChatInput';
import Loading from '../common/Loading';
import CampaignPreview from '../Campaign/CampaignPreview';
import { sendMessage } from '../../services/chat';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [campaignData, setCampaignData] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    setMessages(prev => [...prev, { type: 'user', content: text }]);
    setLoading(true);

    try {
      const response = await sendMessage(text);
      setMessages(prev => [...prev, { type: 'assistant', content: response.message }]);
      if (response.campaignData) {
        setCampaignData(response.campaignData);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: 'Sorry, there was an error processing your message.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 chat-container">
          {messages.map((message, index) => (
            <ChatBubble key={index} {...message} />
          ))}
          {loading && <Loading />}
          <div ref={messagesEndRef} />
        </div>
        <ChatInput onSend={handleSendMessage} disabled={loading} />
      </div>
      {campaignData && (
        <div className="w-96 border-l border-gray-200">
          <CampaignPreview data={campaignData} />
        </div>
      )}
    </div>
  );
};

export default ChatInterface;