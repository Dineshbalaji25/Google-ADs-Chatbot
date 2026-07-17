import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';
import Loading from '../common/Loading';

const AdminTemplates = () => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Form states for active editing
  const [category, setCategory] = useState('');
  const [headlines, setHeadlines] = useState([]);
  const [descriptions, setDescriptions] = useState([]);
  const [keywords, setKeywords] = useState([]);

  // Input fields state
  const [newHeadline, setNewHeadline] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newKeyword, setNewKeyword] = useState('');

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/api/admin/templates');
      setTemplates(data);
      if (data.length > 0) {
        loadTemplateIntoForm(data[0]);
      }
    } catch (err) {
      console.error('Error fetching templates:', err);
      setError('Failed to fetch templates.');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplateIntoForm = (template) => {
    setSelectedTemplate(template);
    setCategory(template.category);
    setHeadlines(template.headlines || []);
    setDescriptions(template.descriptions || []);
    setKeywords(template.keywords || []);
  };

  const handleAddNew = () => {
    setSelectedTemplate(null);
    setCategory('');
    setHeadlines([]);
    setDescriptions([]);
    setKeywords([]);
  };

  const handleAddHeadline = () => {
    if (!newHeadline.trim()) return;
    setHeadlines(prev => [...prev, newHeadline.trim()]);
    setNewHeadline('');
  };

  const handleAddDescription = () => {
    if (!newDescription.trim()) return;
    setDescriptions(prev => [...prev, newDescription.trim()]);
    setNewDescription('');
  };

  const handleAddKeyword = () => {
    if (!newKeyword.trim()) return;
    setKeywords(prev => [...prev, newKeyword.trim()]);
    setNewKeyword('');
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!category.trim()) {
      setError('Category name is required.');
      return;
    }

    const payload = {
      category: category.toLowerCase().trim(),
      headlines,
      descriptions,
      keywords
    };

    try {
      if (selectedTemplate) {
        await apiClient.put(`/api/admin/templates/${selectedTemplate.id}`, payload);
        setSuccess('Template updated successfully!');
      } else {
        await apiClient.post('/api/admin/templates', payload);
        setSuccess('New category template created successfully!');
      }
      fetchTemplates();
    } catch (err) {
      console.error('Error saving template:', err);
      setError(err.message || 'Failed to save template.');
    }
  };

  if (loading && templates.length === 0) {
    return (
      <div className="p-6 flex justify-center items-center h-full">
        <Loading />
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto bg-white dark:bg-slate-900 transition-colors duration-200">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100">
          Template Admin
        </h2>
        <button
          onClick={handleAddNew}
          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
        >
          + Add Category
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Categories Sidebar */}
        <div className="col-span-1 border-r border-slate-100 dark:border-slate-800 pr-4 space-y-1">
          <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-2">
            Categories
          </span>
          {templates.map((t) => (
            <button
              key={t.id}
              onClick={() => loadTemplateIntoForm(t)}
              className={`w-full text-left p-2.5 rounded-lg text-sm transition-colors block ${
                selectedTemplate?.id === t.id
                  ? 'bg-blue-50 dark:bg-blue-950/20 text-blue-600 dark:text-blue-400 font-semibold'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'
              }`}
            >
              {t.category.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Editor Form */}
        <form onSubmit={handleSave} className="col-span-2 space-y-4">
          {error && (
            <div className="bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 dark:bg-green-950/20 text-green-600 dark:text-green-400 p-3 rounded-lg text-sm">
              {success}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
              Category Name
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={!!selectedTemplate}
              placeholder="e.g. restaurant, retail, fitness"
              className="w-full p-2 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-55"
            />
          </div>

          {/* Headlines Editor */}
          <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800/50">
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
              Default Headlines
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder="Add headline template (e.g. Best {cuisine} dining)..."
                value={newHeadline}
                onChange={(e) => setNewHeadline(e.target.value)}
                className="flex-1 p-2 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 rounded-lg text-xs"
              />
              <button
                type="button"
                onClick={handleAddHeadline}
                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-lg text-xs"
              >
                Add
              </button>
            </div>
            <ul className="space-y-1 max-h-32 overflow-y-auto">
              {headlines.map((hl, idx) => (
                <li key={idx} className="flex justify-between items-center bg-white dark:bg-slate-900 p-2 rounded border border-slate-100 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
                  <span className="truncate">{hl}</span>
                  <button
                    type="button"
                    onClick={() => setHeadlines(prev => prev.filter((_, i) => i !== idx))}
                    className="text-red-500 hover:text-red-700 px-1 font-semibold"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Descriptions Editor */}
          <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800/50">
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
              Default Descriptions
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder="Add description template..."
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                className="flex-1 p-2 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 rounded-lg text-xs"
              />
              <button
                type="button"
                onClick={handleAddDescription}
                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-lg text-xs"
              >
                Add
              </button>
            </div>
            <ul className="space-y-1 max-h-32 overflow-y-auto">
              {descriptions.map((desc, idx) => (
                <li key={idx} className="flex justify-between items-center bg-white dark:bg-slate-900 p-2 rounded border border-slate-100 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
                  <span className="truncate">{desc}</span>
                  <button
                    type="button"
                    onClick={() => setDescriptions(prev => prev.filter((_, i) => i !== idx))}
                    className="text-red-500 hover:text-red-700 px-1 font-semibold"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Keywords Editor */}
          <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800/50">
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
              Default Keywords
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder="Add keyword template (e.g. {cuisine} restaurant)..."
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                className="flex-1 p-2 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 rounded-lg text-xs"
              />
              <button
                type="button"
                onClick={handleAddKeyword}
                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-lg text-xs"
              >
                Add
              </button>
            </div>
            <ul className="space-y-1 max-h-32 overflow-y-auto">
              {keywords.map((kw, idx) => (
                <li key={idx} className="flex justify-between items-center bg-white dark:bg-slate-900 p-2 rounded border border-slate-100 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
                  <span className="truncate">{kw}</span>
                  <button
                    type="button"
                    onClick={() => setKeywords(prev => prev.filter((_, i) => i !== idx))}
                    className="text-red-500 hover:text-red-700 px-1 font-semibold"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <button
            type="submit"
            className="w-full bg-green-500 hover:bg-green-600 text-white p-2.5 rounded-lg text-sm font-semibold transition-colors"
          >
            Save Template Config
          </button>
        </form>
      </div>
    </div>
  );
};

export default AdminTemplates;
