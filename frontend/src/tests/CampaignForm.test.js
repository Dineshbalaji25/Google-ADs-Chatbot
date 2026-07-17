// tests/CampaignForm.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import CampaignForm from '../components/Campaign/CampaignForms';

describe('CampaignForm Component', () => {
  const mockData = {
    headlines: ['Pizza Party', 'Best NYC Pizza'],
    descriptions: ['Fresh NYC Pizza straight from oven.'],
    keywords: ['pizza', 'best pizza'],
    daily_budget: 15,
    location: 'New York'
  };

  test('renders form inputs with initial data', () => {
    render(<CampaignForm data={mockData} onSave={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByPlaceholderText(/e.g. New York/i)).toHaveValue('New York');
    expect(screen.getByRole('spinbutton')).toHaveValue(15);
    expect(screen.getByText('Pizza Party')).toBeInTheDocument();
    expect(screen.getByText('Best NYC Pizza')).toBeInTheDocument();
  });

  test('adds and removes headlines within constraints', () => {
    render(<CampaignForm data={mockData} onSave={vi.fn()} onCancel={vi.fn()} />);

    const input = screen.getByPlaceholderText(/Add headline/i);
    const addButton = screen.getAllByRole('button', { name: /Add/i })[0];

    // Add a new headline
    fireEvent.change(input, { target: { value: 'Third Headline' } });
    fireEvent.click(addButton);

    expect(screen.getByText('Third Headline')).toBeInTheDocument();

    // Remove a headline
    const removeButtons = screen.getAllByRole('button', { name: /Remove/i });
    fireEvent.click(removeButtons[0]); // removes Pizza Party

    expect(screen.queryByText('Pizza Party')).not.toBeInTheDocument();
  });

  test('calls onCancel when Cancel button is clicked', () => {
    const handleCancel = vi.fn();
    render(<CampaignForm data={mockData} onSave={vi.fn()} onCancel={handleCancel} />);

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelButton);

    expect(handleCancel).toHaveBeenCalledTimes(1);
  });
});
