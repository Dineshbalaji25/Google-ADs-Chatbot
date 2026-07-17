// tests/CampaignPreview.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import CampaignPreview from '../components/Campaign/CampaignPreview';

describe('CampaignPreview Component', () => {
  const mockData = {
    headlines: ['Pizza Oven Special', 'NYC Best Pizza'],
    description: 'Hot pizza delivered in 30 minutes in Manhattan.',
    keywords: ['manhattan pizza', 'best food nyc'],
    daily_budget: 20.0,
    location: 'Manhattan, NY',
    estimated_metrics: {
      impressions: '10K - 15K',
      clicks: '500 - 800',
      ctr: '5.2%',
      average_cpc: '$0.80',
      cost: '$400 - $640'
    }
  };

  test('renders location, budget, and generated copy', () => {
    render(<CampaignPreview data={mockData} onEdit={vi.fn()} onCreate={vi.fn()} />);

    expect(screen.getByText('Manhattan, NY')).toBeInTheDocument();
    expect(screen.getByText('$20')).toBeInTheDocument();
    expect(screen.getByText('Pizza Oven Special')).toBeInTheDocument();
    expect(screen.getByText('NYC Best Pizza')).toBeInTheDocument();
    expect(screen.getByText('Hot pizza delivered in 30 minutes in Manhattan.')).toBeInTheDocument();
    expect(screen.getByText('manhattan pizza')).toBeInTheDocument();
  });

  test('renders estimated metrics values', () => {
    render(<CampaignPreview data={mockData} onEdit={vi.fn()} onCreate={vi.fn()} />);

    expect(screen.getByText('10K - 15K')).toBeInTheDocument();
    expect(screen.getByText(/5\.2/)).toBeInTheDocument();
    expect(screen.getByText(/0\.80/)).toBeInTheDocument();
  });

  test('clicks call edit action prop', () => {
    const handleEdit = vi.fn();
    render(<CampaignPreview data={mockData} onEdit={handleEdit} onCreate={vi.fn()} />);

    const editBtn = screen.getByRole('button', { name: /Edit/i });
    fireEvent.click(editBtn);

    expect(handleEdit).toHaveBeenCalledTimes(1);
  });
});
