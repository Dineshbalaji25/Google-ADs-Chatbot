// components/Campaign/CampaignPreview.js
import React from 'react';
import Button from '../common/Button';

const CampaignPreview = ({ data, onEdit, onCreate }) => {
  const handleExportPDF = () => {
    const printContent = `
      <html>
        <head>
          <title>Google Ads Campaign Draft</title>
          <style>
            body { font-family: sans-serif; padding: 40px; color: #333; }
            h1 { font-size: 24px; color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            section { margin-bottom: 20px; background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; }
            h3 { font-size: 14px; margin-top: 0; color: #475569; }
            .value { font-size: 16px; font-weight: bold; color: #0f172a; }
            .item { background: white; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px; margin-bottom: 8px; font-size: 14px; }
            .badge { display: inline-block; background: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 12px; font-size: 12px; margin-right: 6px; margin-top: 6px; font-weight: 600; }
            .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
          </style>
        </head>
        <body>
          <h1>Google Ads Campaign Draft</h1>
          
          <section>
            <h3>Target Location</h3>
            <div class="value">${data.location || 'Online'}</div>
          </section>

          <section>
            <h3>Daily Budget</h3>
            <div class="value">$${data.daily_budget || 10}</div>
          </section>

          <section>
            <h3>Headlines</h3>
            ${(data.headlines || []).map(hl => `<div class="item">${hl}</div>`).join('')}
          </section>

          <section>
            <h3>Description</h3>
            <div class="item">${data.description || (data.descriptions && data.descriptions[0]) || ''}</div>
          </section>

          <section>
            <h3>Keywords</h3>
            <div>
              ${(data.keywords || []).map(kw => `<span class="badge">${kw}</span>`).join('')}
            </div>
          </section>

          <section>
            <h3>Estimated Performance (Monthly)</h3>
            <div class="grid">
              <div class="item">Impressions: <strong>${data.estimated_metrics?.impressions || '10K - 15K'}</strong></div>
              <div class="item">Clicks: <strong>${data.estimated_metrics?.clicks || '500 - 800'}</strong></div>
              <div class="item">CTR: <strong>${data.estimated_metrics?.ctr || '5.2'}%</strong></div>
              <div class="item">Avg CPC: <strong>$${data.estimated_metrics?.average_cpc || '0.80'}</strong></div>
            </div>
          </section>

          <script>
            window.onload = function() {
              window.print();
              setTimeout(function() { window.close(); }, 500);
            }
          </script>
        </body>
      </html>
    `;
    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
  };

  return (
    <div className="h-full overflow-y-auto p-4 bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-slate-800 transition-colors duration-200">
      <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-slate-100">Campaign Preview</h2>
      
      <div className="space-y-4">
        {data.location && (
          <section className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
            <h3 className="font-medium text-gray-700 dark:text-slate-300 mb-1">Target Location</h3>
            <div className="text-sm font-semibold text-gray-900 dark:text-slate-100">{data.location}</div>
          </section>
        )}

        {data.daily_budget && (
          <section className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
            <h3 className="font-medium text-gray-700 dark:text-slate-300 mb-1">Daily Budget</h3>
            <div className="text-sm font-semibold text-gray-900 dark:text-slate-100">${data.daily_budget}</div>
          </section>
        )}

        <section className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
          <h3 className="font-medium text-gray-700 dark:text-slate-300 mb-2">Headlines</h3>
          {data.headlines && data.headlines.map((headline, index) => (
            <div key={index} className="bg-white dark:bg-slate-900 p-2 rounded border border-gray-100 dark:border-slate-800 mb-2 text-sm text-gray-850 dark:text-slate-200">
              {headline}
            </div>
          ))}
        </section>

        <section className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
          <h3 className="font-medium text-gray-700 dark:text-slate-300 mb-2">Description</h3>
          <div className="bg-white dark:bg-slate-900 p-2 rounded border border-gray-100 dark:border-slate-800 text-sm text-gray-850 dark:text-slate-200">
            {data.description || (data.descriptions && data.descriptions[0])}
          </div>
        </section>

        <section className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
          <h3 className="font-medium text-gray-700 dark:text-slate-300 mb-2">Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {data.keywords && data.keywords.map((keyword, index) => (
              <span
                key={index}
                className="bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-3 py-1 rounded-full text-xs font-semibold"
              >
                {keyword}
              </span>
            ))}
          </div>
        </section>

        {data.estimated_metrics && (
          <section className="bg-gray-50 dark:bg-slate-800 p-4 rounded-lg">
            <h3 className="font-medium text-gray-700 dark:text-slate-300 mb-2">Estimated Metrics</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-white dark:bg-slate-900 p-2 rounded border border-gray-100 dark:border-slate-800">
                <span className="text-gray-500 dark:text-slate-400 block">Impressions</span>
                <span className="font-bold text-gray-900 dark:text-slate-100">{data.estimated_metrics.impressions}</span>
              </div>
              <div className="bg-white dark:bg-slate-900 p-2 rounded border border-gray-100 dark:border-slate-800">
                <span className="text-gray-500 dark:text-slate-400 block">Clicks</span>
                <span className="font-bold text-gray-900 dark:text-slate-100">{data.estimated_metrics.clicks}</span>
              </div>
              <div className="bg-white dark:bg-slate-900 p-2 rounded border border-gray-100 dark:border-slate-800">
                <span className="text-gray-500 dark:text-slate-400 block">CTR</span>
                <span className="font-bold text-gray-900 dark:text-slate-100">{data.estimated_metrics.ctr}%</span>
              </div>
              <div className="bg-white dark:bg-slate-900 p-2 rounded border border-gray-100 dark:border-slate-800">
                <span className="text-gray-500 dark:text-slate-400 block">Avg CPC</span>
                <span className="font-bold text-gray-900 dark:text-slate-100">${data.estimated_metrics.average_cpc}</span>
              </div>
            </div>
          </section>
        )}

        <div className="flex flex-col gap-2 pt-2 pb-6">
          <Button
            onClick={onCreate || data.onCreateCampaign}
            className="w-full"
            variant="success"
          >
            Create Campaign
          </Button>
          <Button
            onClick={onEdit}
            className="w-full"
            variant="primary"
          >
            Edit Campaign
          </Button>
          <Button
            onClick={handleExportPDF}
            className="w-full bg-amber-500 hover:bg-amber-600 text-white"
          >
            Export Draft PDF
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CampaignPreview;