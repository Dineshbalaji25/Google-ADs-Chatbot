// components/Campaign/CampaignPreview.js
import React from 'react';
import { FileDown, Pencil, Rocket, Search } from 'lucide-react';
import Button from '../common/Button';

const first = (values, fallback = '') => Array.isArray(values) && values.length ? values[0] : fallback;

const getDescription = (preview) => preview.description || first(preview.descriptions);
const getPrimaryText = (preview) => preview.primary_text || first(preview.primary_texts);

const platformLabel = (platform) => (platform === 'meta' ? 'Meta' : 'Google');

const getPreviewItems = (data) => {
  if (data.platform === 'both') {
    return [
      { platform: 'google', preview: data.previews?.google || data },
      { platform: 'meta', preview: data.previews?.meta || data },
    ];
  }
  return [{ platform: data.platform || 'google', preview: data }];
};

const formatMetricValue = (value, suffix = '') => {
  if (value === undefined || value === null || value === '') return '-';
  return `${value}${suffix}`;
};

const GooglePreviewCard = ({ preview }) => {
  const headlines = preview.headlines || [];
  const descriptions = preview.descriptions || [];

  return (
    <section className="rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 mb-3">
        <Search size={14} />
        <span>Google Search</span>
      </div>
      <div className="rounded-md border border-slate-100 dark:border-slate-800 p-3 bg-slate-50 dark:bg-slate-900">
        <div className="text-[11px] text-emerald-700 dark:text-emerald-400 truncate">
          Ad - {preview.link_url || 'example.com'}
        </div>
        <div className="mt-1 text-[15px] leading-snug font-medium text-blue-700 dark:text-blue-300">
          {headlines.slice(0, 2).join(' | ') || 'Campaign headline'}
        </div>
        <div className="mt-1 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
          {getDescription(preview) || 'Campaign description'}
        </div>
        {descriptions[1] && (
          <div className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
            {descriptions[1]}
          </div>
        )}
      </div>
    </section>
  );
};

const MetaPreviewCard = ({ preview }) => {
  const headline = first(preview.headlines, 'Campaign headline');
  const description = getDescription(preview) || 'Campaign description';
  const primaryText = getPrimaryText(preview) || 'Primary text for your feed ad.';
  const cta = (preview.call_to_action || 'LEARN_MORE').replace(/_/g, ' ');

  return (
    <section className="rounded-md border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 overflow-hidden">
      <div className="p-3 flex items-center gap-2">
        <div className="h-8 w-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
          f
        </div>
        <div className="min-w-0">
          <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
            Page {preview.page_id || 'mock'}
          </div>
          <div className="text-[10px] text-slate-500 dark:text-slate-400">Sponsored</div>
        </div>
      </div>
      <div className="px-3 pb-3 text-xs leading-relaxed text-slate-800 dark:text-slate-200">
        {primaryText}
      </div>
      {preview.asset_url ? (
        <img
          src={preview.asset_url}
          alt="Meta ad asset"
          className="w-full aspect-[1.91/1] object-cover bg-slate-100 dark:bg-slate-900"
        />
      ) : (
        <div className="w-full aspect-[1.91/1] bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-xs font-semibold text-slate-500 dark:text-slate-400">
          Image or video asset
        </div>
      )}
      <div className="flex items-center gap-2 p-3 bg-slate-100 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
        <div className="min-w-0 flex-1">
          <div className="text-[10px] uppercase text-slate-500 dark:text-slate-400 truncate">
            {preview.link_url || 'example.com'}
          </div>
          <div className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">{headline}</div>
          <div className="text-[11px] text-slate-600 dark:text-slate-400 truncate">{description}</div>
        </div>
        <span className="shrink-0 rounded bg-slate-200 dark:bg-slate-700 px-2 py-1 text-[10px] font-bold text-slate-700 dark:text-slate-200">
          {cta}
        </span>
      </div>
    </section>
  );
};

const MetricsPanel = ({ preview, platform }) => {
  const metrics = preview.estimated_metrics || {};
  const metricRows = platform === 'meta'
    ? [
        ['Reach', metrics.reach],
        ['Impressions', metrics.impressions],
        ['Clicks', metrics.clicks],
        ['CTR', formatMetricValue(metrics.ctr, '%')],
      ]
    : [
        ['Impressions', metrics.impressions],
        ['Clicks', metrics.clicks],
        ['CTR', formatMetricValue(metrics.ctr, '%')],
        ['Avg CPC', metrics.average_cpc ? `$${metrics.average_cpc}` : '-'],
      ];

  return (
    <section className="rounded-md bg-slate-50 dark:bg-slate-900 p-3">
      <h3 className="font-medium text-slate-700 dark:text-slate-300 mb-2 text-sm">
        {platformLabel(platform)} Metrics
      </h3>
      <div className="grid grid-cols-2 gap-2 text-xs">
        {metricRows.map(([label, value]) => (
          <div key={label} className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-100 dark:border-slate-800">
            <span className="text-slate-500 dark:text-slate-400 block">{label}</span>
            <span className="font-bold text-slate-900 dark:text-slate-100">{value || '-'}</span>
          </div>
        ))}
      </div>
    </section>
  );
};

const PreviewBlock = ({ platform, preview }) => (
  <div className="space-y-3 min-w-0">
    {platform === 'meta' ? <MetaPreviewCard preview={preview} /> : <GooglePreviewCard preview={preview} />}

    <section className="rounded-md bg-slate-50 dark:bg-slate-900 p-3">
      <h3 className="font-medium text-slate-700 dark:text-slate-300 mb-2 text-sm">Draft Copy</h3>
      <div className="space-y-2">
        {(preview.headlines || []).slice(0, 5).map((headline, index) => (
          <div key={`${platform}-headline-${index}`} className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-100 dark:border-slate-800 text-xs text-slate-850 dark:text-slate-200">
            {headline}
          </div>
        ))}
        {platform === 'meta' && getPrimaryText(preview) && (
          <div className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-100 dark:border-slate-800 text-xs text-slate-850 dark:text-slate-200">
            {getPrimaryText(preview)}
          </div>
        )}
      </div>
    </section>

    {platform === 'google' && preview.keywords?.length > 0 && (
      <section className="rounded-md bg-slate-50 dark:bg-slate-900 p-3">
        <h3 className="font-medium text-slate-700 dark:text-slate-300 mb-2 text-sm">Keywords</h3>
        <div className="flex flex-wrap gap-2">
          {preview.keywords.map((keyword, index) => (
            <span
              key={index}
              className="bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2.5 py-1 rounded-full text-[11px] font-semibold"
            >
              {keyword}
            </span>
          ))}
        </div>
      </section>
    )}

    {preview.estimated_metrics && <MetricsPanel preview={preview} platform={platform} />}
  </div>
);

const CampaignPreview = ({ data = {}, onEdit, onCreate }) => {
  const previewItems = getPreviewItems(data);

  const handleExportPDF = () => {
    const sections = previewItems.map(({ platform, preview }) => `
      <section>
        <h2>${platformLabel(platform)} Campaign Draft</h2>
        <h3>Location</h3><div class="value">${preview.location || data.location || 'Online'}</div>
        <h3>Daily Budget</h3><div class="value">$${preview.daily_budget || data.daily_budget || 10}</div>
        <h3>Copy</h3>
        ${(preview.headlines || []).map(hl => `<div class="item">${hl}</div>`).join('')}
        ${getPrimaryText(preview) ? `<div class="item">${getPrimaryText(preview)}</div>` : ''}
        <div class="item">${getDescription(preview) || ''}</div>
      </section>
    `).join('');

    const printContent = `
      <html>
        <head>
          <title>Ads Campaign Draft</title>
          <style>
            body { font-family: sans-serif; padding: 40px; color: #333; }
            h1 { font-size: 24px; color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            h2 { font-size: 18px; color: #0f172a; }
            section { margin-bottom: 20px; background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; }
            h3 { font-size: 14px; color: #475569; margin-bottom: 6px; }
            .value { font-size: 16px; font-weight: bold; color: #0f172a; margin-bottom: 12px; }
            .item { background: white; padding: 8px; border: 1px solid #e2e8f0; border-radius: 4px; margin-bottom: 8px; font-size: 14px; }
          </style>
        </head>
        <body>
          <h1>Ads Campaign Draft</h1>
          ${sections}
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
    <div className="h-full overflow-y-auto p-4 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 transition-colors duration-200">
      <div className="flex items-center justify-between gap-3 mb-4">
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">Campaign Preview</h2>
        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 dark:text-slate-400">
          {data.platform === 'both' ? 'Google + Meta' : platformLabel(data.platform || 'google')}
        </span>
      </div>

      <div className="space-y-6">
        {previewItems.map(({ platform, preview }) => (
          <div key={platform} className="space-y-3">
            {previewItems.length > 1 && (
              <h3
                className={`text-sm font-bold uppercase tracking-wide border-b pb-2 ${
                  platform === 'meta'
                    ? 'text-indigo-600 dark:text-indigo-400 border-indigo-100 dark:border-indigo-900'
                    : 'text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-900'
                }`}
              >
                {platformLabel(platform)} Ads
              </h3>
            )}
            <PreviewBlock platform={platform} preview={preview} />
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-2 pt-4 pb-6">
        <Button onClick={onCreate || data.onCreateCampaign} className="w-full" variant="success">
          <Rocket size={16} className="inline-block mr-2" />
          Create Campaign
        </Button>
        <Button onClick={onEdit} className="w-full" variant="primary">
          <Pencil size={16} className="inline-block mr-2" />
          Edit Campaign
        </Button>
        <Button onClick={handleExportPDF} className="w-full bg-amber-500 hover:bg-amber-600 text-white">
          <FileDown size={16} className="inline-block mr-2" />
          Export Draft PDF
        </Button>
      </div>
    </div>
  );
};

export default CampaignPreview;