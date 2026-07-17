// services/chat.js
import { apiClient } from './api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const sendMessage = async (content) => {
  try {
    let sessionId = sessionStorage.getItem('chat_session_id');
    if (!sessionId) {
      sessionId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
      sessionStorage.setItem('chat_session_id', sessionId);
    }
    const response = await apiClient.post('/api/chat', { content, session_id: sessionId });
    return response;
  } catch (error) {
    console.error('Chat service error:', error);
    throw error;
  }
};

export const sendStreamingMessage = async (content, onToken, onBusinessInfo, onCampaignData) => {
  let sessionId = sessionStorage.getItem('chat_session_id');
  if (!sessionId) {
    sessionId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    sessionStorage.setItem('chat_session_id', sessionId);
  }

  const token = localStorage.getItem('auth_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };

  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ content, session_id: sessionId })
  });

  if (response.status === 401) {
    localStorage.removeItem('auth_token');
    window.location.reload();
    return;
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let currentEvent = null;

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith('event:')) {
        currentEvent = trimmed.slice(6).trim();
      } else if (trimmed.startsWith('data:')) {
        const dataStr = trimmed.slice(5).trim();
        try {
          const parsed = JSON.parse(dataStr);
          if (currentEvent === 'token') {
            onToken(parsed);
          } else if (currentEvent === 'business_info') {
            onBusinessInfo(parsed);
          } else if (currentEvent === 'campaign_data') {
            onCampaignData(parsed);
          }
        } catch (e) {
          console.error('Failed to parse SSE line data:', e);
        }
      }
    }
  }
};

export const generateCampaignPreview = async (businessInfo) => {
  try {
    const response = await apiClient.post('/api/campaign/preview', businessInfo);
    return response;
  } catch (error) {
    console.error('Campaign preview error:', error);
    throw error;
  }
};

export const createCampaign = async (campaignData) => {
  try {
    const response = await apiClient.post('/api/campaign/create', campaignData);
    return response;
  } catch (error) {
    console.error('Campaign creation error:', error);
    throw error;
  }
};