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
  const platform = data.platform || 'google';
  const isMeta = platform === 'meta' || platform === 'both';
  const isGoogle = platform === 'google' || platform === 'both';

  const limits = {
    headlines: { maxCount: isGoogle ? 15 : 3, maxLength: isGoogle ? 30 : 40 },
    descriptions: { maxCount: isGoogle ? 4 : 3, maxLength: isGoogle ? 90 : 30 },
    primaryTexts: { maxCount: 3, maxLength: 125 }
  };

  const [headlines, setHeadlines] = useState(data.headlines || []);
  const [newHeadline, setNewHeadline] = useState('');
  
  const [descriptions, setDescriptions] = useState(data.descriptions || [data.description || '']);
  const [newDescription, setNewDescription] = useState('');

  const [primaryTexts, setPrimaryTexts] = useState(data.primary_texts || (data.primary_text ? [data.primary_text] : []));
  const [newPrimaryText, setNewPrimaryText] = useState('');

  const [keywords, setKeywords] = useState(data.keywords || []);
  const [newKeyword, setNewKeyword] = useState('');

  const [dailyBudget, setDailyBudget] = useState(data.daily_budget || 10);
  const [location, setLocation] = useState(data.location || 'New York');

  const [assetUrl, setAssetUrl] = useState(data.asset_url || '');
  const [videoId, setVideoId] = useState(data.video_id || '');


  const [errors, setErrors] = useState({});

  // Headlines Action handlers
  const handleAddHeadline = () => {
    if (!newHeadline.trim()) return;
    if (headlines.length >= limits.headlines.maxCount) {
      setErrors(prev => ({ ...prev, headlines: `Max ${limits.headlines.maxCount} headlines allowed` }));
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
    if (descriptions.length >= limits.descriptions.maxCount) {
      setErrors(prev => ({ ...prev, descriptions: `Max ${limits.descriptions.maxCount} descriptions allowed` }));
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

  // Primary Texts Action handlers
  const handleAddPrimaryText = () => {
    if (!newPrimaryText.trim()) return;
    if (primaryTexts.length >= limits.primaryTexts.maxCount) {
      setErrors(prev => ({ ...prev, primaryTexts: `Max ${limits.primaryTexts.maxCount} primary texts allowed` }));
      return;
    }
    setPrimaryTexts([...primaryTexts, newPrimaryText.trim()]);
    setNewPrimaryText('');
    setErrors(prev => ({ ...prev, primaryTexts: null }));
  };

  const handleRemovePrimaryText = (index) => {
    const next = primaryTexts.filter((_, i) => i !== index);
    setPrimaryTexts(next);
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

    if (headlines.length < 1 || headlines.length > limits.headlines.maxCount) {
      newErrors.headlines = `Must have between 1 and ${limits.headlines.maxCount} headlines`;
    }
    if (descriptions.length < 1 || descriptions.length > limits.descriptions.maxCount) {
      newErrors.descriptions = `Must have between 1 and ${limits.descriptions.maxCount} descriptions`;
    }
    if (isMeta && (primaryTexts.length < 1 || primaryTexts.length > limits.primaryTexts.maxCount)) {
      newErrors.primaryTexts = `Must have between 1 and ${limits.primaryTexts.maxCount} primary texts`;
    }
    if (keywords.length < 1 && isGoogle) {
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
      primary_texts: primaryTexts,
      primary_text: primaryTexts[0],
      keywords,
      daily_budget: Number(dailyBudget),
      location,
      asset_url: assetUrl,
      video_id: videoId
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
            Headlines ({headlines.length}/{limits.headlines.maxCount})
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newHeadline}
              onChange={(e) => setNewHeadline(e.target.value)}
              maxLength={limits.headlines.maxLength}
              className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={`Add headline (max ${limits.headlines.maxLength} chars)...`}
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
            Descriptions ({descriptions.length}/{limits.descriptions.maxCount})
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              maxLength={limits.descriptions.maxLength}
              className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={`Add description (max ${limits.descriptions.maxLength} chars)...`}
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

        {/* Primary Texts Section (Meta Only) */}
        {isMeta && (
          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
            <label className="block text-sm font-semibold text-gray-700 mb-1">
              Primary Texts ({primaryTexts.length}/{limits.primaryTexts.maxCount})
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newPrimaryText}
                onChange={(e) => setNewPrimaryText(e.target.value)}
                maxLength={limits.primaryTexts.maxLength}
                className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={`Add primary text (max ${limits.primaryTexts.maxLength} chars)...`}
              />
              <Button type="button" onClick={handleAddPrimaryText} className="px-3">Add</Button>
            </div>
            {errors.primaryTexts && <p className="text-red-500 text-xs mb-2">{errors.primaryTexts}</p>}
            <ul className="space-y-1 max-h-40 overflow-y-auto">
              {primaryTexts.map((text, idx) => (
                <li key={idx} className="flex justify-between items-center bg-white p-2 rounded border text-sm">
                  <span className="truncate flex-1 pr-2">{text}</span>
                  <button
                    type="button"
                    onClick={() => handleRemovePrimaryText(idx)}
                    className="text-red-500 hover:text-red-700 text-xs font-semibold px-2"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Media Assets Section (Meta Only) */}
        {isMeta && (
          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">Media Assets</h3>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Image Asset URL</label>
              <input
                type="url"
                value={assetUrl}
                onChange={(e) => setAssetUrl(e.target.value)}
                className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
                placeholder="https://example.com/image.jpg"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Or Video ID</label>
              <input
                type="text"
                value={videoId}
                onChange={(e) => setVideoId(e.target.value)}
                className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
                placeholder="Video ID"
              />
            </div>
          </div>
        )}

        {/* Keywords Section */}
        {isGoogle && (
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
        )}

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