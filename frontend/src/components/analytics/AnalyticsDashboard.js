import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { apiClient } from '../../services/api';
import Loading from '../common/Loading';

const AnalyticsDashboard = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get('/api/campaigns');
      setCampaigns(data);
      if (data.length > 0) {
        setSelectedCampaign(data[0].id);
      }
    } catch (err) {
      console.error('Error fetching campaigns:', err);
      setError('Failed to load campaigns.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedCampaign) {
      fetchMetrics(selectedCampaign);
    }
  }, [selectedCampaign]);

  const fetchMetrics = async (campaignId) => {
    try {
      const response = await apiClient.get(`/api/campaigns/${campaignId}/metrics`);
      setMetrics(response.metrics || []);
    } catch (err) {
      console.error('Error fetching campaign metrics:', err);
    }
  };

  if (loading && campaigns.length === 0) {
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
          Campaign Analytics
        </h2>
        {campaigns.length > 0 && (
          <select
            value={selectedCampaign || ''}
            onChange={(e) => setSelectedCampaign(e.target.value)}
            className="p-2 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {campaigns.map((camp) => (
              <option key={camp.id} value={camp.id}>
                {camp.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 p-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      {campaigns.length === 0 ? (
        <div className="text-center text-slate-400 dark:text-slate-500 py-10">
          <p className="text-sm">No campaigns created yet. Create a campaign first to see performance analytics!</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Main Chart Card */}
          <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800/80">
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4">
              Performance Trend (Last 7 Days)
            </h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:hidden" />
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" className="hidden dark:block" />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
                  <YAxis yAxisId="left" stroke="#3b82f6" fontSize={11} />
                  <YAxis yAxisId="right" orientation="right" stroke="#10b981" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(30, 41, 59, 0.9)', 
                      border: 'none', 
                      borderRadius: '8px',
                      color: '#f8fafc'
                    }} 
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="clicks" 
                    name="Clicks" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    activeDot={{ r: 6 }} 
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="spend" 
                    name="Spend ($)" 
                    stroke="#10b981" 
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Quick Metrics grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50/50 dark:bg-blue-950/10 p-4 rounded-xl border border-blue-100/50 dark:border-blue-900/20">
              <span className="text-xs text-blue-600 dark:text-blue-400 font-semibold block mb-1">Total Impressions</span>
              <span className="text-lg font-bold text-blue-900 dark:text-blue-300">
                {metrics.reduce((acc, curr) => acc + (curr.impressions || 0), 0).toLocaleString()}
              </span>
            </div>
            <div className="bg-emerald-50/50 dark:bg-emerald-950/10 p-4 rounded-xl border border-emerald-100/50 dark:border-emerald-900/20">
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold block mb-1">Total Click Spend</span>
              <span className="text-lg font-bold text-emerald-900 dark:text-emerald-300">
                ${metrics.reduce((acc, curr) => acc + (curr.spend || 0), 0).toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
