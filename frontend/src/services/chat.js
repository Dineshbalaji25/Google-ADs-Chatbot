// services/chat.js
import { apiClient } from './api';

export const sendMessage = async (content) => {
  try {
    const response = await apiClient.post('/api/chat', { content });
    return response;
  } catch (error) {
    console.error('Chat service error:', error);
    throw error;
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