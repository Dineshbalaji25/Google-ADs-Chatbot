// components/Campaign/CampaignForm.js
import React, { useState } from 'react';
import Button from '../common/Button';

const suggestMatchType = (keyword) => {
  const kw = keyword.trim().toLowerCase();
  if (!kw) return '';
  const wordCount = kw.split(/\s+/).filter(Boolean).length;
  if (wordCount === 1) return 'exact';
  if (wordCount > 3) return 'phrase';
  return 'broad';
};

const CampaignForm = ({ data, onSave, onCancel }) => {
  const [headlines, setHeadlines] = useState(data.headlines || []);
  const [newHeadline, setNewHeadline] = useState('');
  
  const [description, setDescription] = useState(data.description || '');
  // Supporting a list of descriptions as required (1-4 descriptions)
  const [descriptions, setDescriptions] = useState(data.descriptions || [data.description || '']);
  const [newDescription, setNewDescription] = useState('');

  const [keywords, setKeywords] = useState(data.keywords || []);
  const [newKeyword, setNewKeyword] = useState('');

  const [dailyBudget, setDailyBudget] = useState(data.daily_budget || 10);
  const [location, setLocation] = useState(data.location || 'New York');

  const [errors, setErrors] = useState({});

  // Headlines Action handlers
  const handleAddHeadline = () => {
    if (!newHeadline.trim()) return;
    if (headlines.length >= 15) {
      setErrors(prev => ({ ...prev, headlines: 'Max 15 headlines allowed' }));
      return;
    }
    setHeadlines([...headlines, newHeadline.trim()]);
    setNewHeadline('');
    setErrors(prev => ({ ...prev, headlines: null }));
  };

  const handleRemoveHeadline = (index) => {
    const next = headlines.filter((_, i) => i !== index);
    setHeadlines(next);
  };

  // Descriptions Action handlers
  const handleAddDescription = () => {
    if (!newDescription.trim()) return;
    if (descriptions.length >= 4) {
      setErrors(prev => ({ ...prev, descriptions: 'Max 4 descriptions allowed' }));
      return;
    }
    setDescriptions([...descriptions, newDescription.trim()]);
    setNewDescription('');
    setErrors(prev => ({ ...prev, descriptions: null }));
  };

  const handleRemoveDescription = (index) => {
    const next = descriptions.filter((_, i) => i !== index);
    setDescriptions(next);
  };

  // Keywords Action handlers
  const handleAddKeyword = () => {
    if (!newKeyword.trim()) return;
    setKeywords([...keywords, newKeyword.trim()]);
    setNewKeyword('');
  };

  const handleRemoveKeyword = (index) => {
    const next = keywords.filter((_, i) => i !== index);
    setKeywords(next);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};

    if (headlines.length < 1 || headlines.length > 15) {
      newErrors.headlines = 'Must have between 1 and 15 headlines';
    }
    if (descriptions.length < 1 || descriptions.length > 4) {
      newErrors.descriptions = 'Must have between 1 and 4 descriptions';
    }
    if (keywords.length < 1) {
      newErrors.keywords = 'Must specify at least 1 keyword';
    }
    if (!dailyBudget || dailyBudget <= 0) {
      newErrors.budget = 'Daily budget must be greater than 0';
    }
    if (!location.trim()) {
      newErrors.location = 'Target location is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSave({
      ...data,
      headlines,
      descriptions,
      description: descriptions[0], // backward compatibility
      keywords,
      daily_budget: Number(dailyBudget),
      location
    });
  };

  return (
    <div className="h-full overflow-y-auto p-4 bg-white border-l border-gray-200">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Edit Campaign</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6 pb-20">
        {/* Location Section */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Target Location</label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="e.g. New York, Online"
          />
          {errors.location && <p className="text-red-500 text-xs mt-1">{errors.location}</p>}
        </div>

        {/* Daily Budget Section */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Daily Budget ($)</label>
          <input
            type="number"
            value={dailyBudget}
            onChange={(e) => setDailyBudget(e.target.value)}
            className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            min="1"
            step="any"
          />
          {errors.budget && <p className="text-red-500 text-xs mt-1">{errors.budget}</p>}
        </div>

        {/* Headlines Section */}
        <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Headlines ({headlines.length}/15)
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newHeadline}
              onChange={(e) => setNewHeadline(e.target.value)}
              maxLength={30}
              className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Add headline (max 30 chars)..."
            />
            <Button type="button" onClick={handleAddHeadline} className="px-3">Add</Button>
          </div>
          {errors.headlines && <p className="text-red-500 text-xs mb-2">{errors.headlines}</p>}
          <ul className="space-y-1 max-h-40 overflow-y-auto">
            {headlines.map((hl, idx) => (
              <li key={idx} className="flex justify-between items-center bg-white p-2 rounded border text-sm">
                <span className="truncate">{hl}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveHeadline(idx)}
                  className="text-red-500 hover:text-red-700 text-xs font-semibold px-2"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Descriptions Section */}
        <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Descriptions ({descriptions.length}/4)
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              maxLength={90}
              className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Add description (max 90 chars)..."
            />
            <Button type="button" onClick={handleAddDescription} className="px-3">Add</Button>
          </div>
          {errors.descriptions && <p className="text-red-500 text-xs mb-2">{errors.descriptions}</p>}
          <ul className="space-y-1 max-h-40 overflow-y-auto">
            {descriptions.map((desc, idx) => (
              <li key={idx} className="flex justify-between items-center bg-white p-2 rounded border text-sm">
                <span className="truncate flex-1 pr-2">{desc}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveDescription(idx)}
                  className="text-red-500 hover:text-red-700 text-xs font-semibold px-2"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Keywords Section */}
        <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Keywords ({keywords.length})
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Add keyword..."
            />
            <Button type="button" onClick={handleAddKeyword} className="px-3">Add</Button>
          </div>
          {newKeyword.trim() && (
            <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
              <span>Suggested Match Type:</span>
              <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-mono font-bold capitalize">
                {suggestMatchType(newKeyword)}
              </span>
            </div>
          )}
          {errors.keywords && <p className="text-red-500 text-xs mb-2">{errors.keywords}</p>}
          <ul className="space-y-1 max-h-40 overflow-y-auto">
            {keywords.map((kw, idx) => (
              <li key={idx} className="flex justify-between items-center bg-white p-2 rounded border text-sm">
                <div className="flex items-center gap-2">
                  <span>{kw}</span>
                  <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded capitalize">
                    {suggestMatchType(kw)}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(idx)}
                  className="text-red-500 hover:text-red-700 text-xs font-semibold px-2"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Form Actions */}
        <div className="flex gap-3 pt-2">
          <Button type="submit" variant="success" className="flex-1">
            Save
          </Button>
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-100 transition-colors text-gray-700 text-sm font-semibold"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default CampaignForm;