// tests/ChatInterface.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import ChatInterface from '../components/chat/ChatInterface';
import { sendStreamingMessage } from '../services/chat';

// Mock the API methods
vi.mock('../services/chat', () => ({
  sendStreamingMessage: vi.fn(),
  createCampaign: vi.fn(),
}));

describe('ChatInterface Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock scrollIntoView which doesn't exist in jsdom environment
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  test('renders initial feed with input', () => {
    render(<ChatInterface />);
    expect(screen.getByPlaceholderText(/Tell me about your business/i)).toBeInTheDocument();
  });

  test('successfully sends message and receives reply', async () => {
    sendStreamingMessage.mockImplementation((content, onToken, onBusinessInfo, onCampaignData) => {
      onToken('Sure! Here is a campaign suggestion.');
      onBusinessInfo({ type: 'retail' });
      onCampaignData({
        headlines: ['Cool Headline'],
        descriptions: ['Cool description copy text.'],
        description: 'Cool description copy text.',
        keywords: ['keyword'],
        estimated_metrics: {
          impressions: '100',
          clicks: '10'
        }
      });
      return Promise.resolve();
    });

    const { container } = render(<ChatInterface />);

    const input = screen.getByPlaceholderText(/Tell me about your business/i);
    const sendButton = container.querySelector('button[type="submit"]');

    // Type a message
    fireEvent.change(input, { target: { value: 'Create a campaign for shoes' } });
    fireEvent.click(sendButton);

    // Assert user message bubble renders
    expect(screen.getByText('Create a campaign for shoes')).toBeInTheDocument();

    // Wait for the mock reply to render
    await waitFor(() => {
      expect(screen.getByText('Sure! Here is a campaign suggestion.')).toBeInTheDocument();
    });

    // Assert campaign preview panel is displayed
    expect(screen.getByText('Cool Headline')).toBeInTheDocument();
  });

  test('handles message send error gracefully', async () => {
    sendStreamingMessage.mockRejectedValue(new Error('Network failure'));

    const { container } = render(<ChatInterface />);

    const input = screen.getByPlaceholderText(/Tell me about your business/i);
    const sendButton = container.querySelector('button[type="submit"]');

    fireEvent.change(input, { target: { value: 'Failure test' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Sorry, there was an error processing your message/i)).toBeInTheDocument();
    });
  });
});
