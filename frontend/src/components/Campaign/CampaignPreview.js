// components/Campaign/CampaignPreview.js
import React from 'react';
import Button from '../common/Button';

const CampaignPreview = ({ data }) => {
  return (
    <div className="h-full overflow-y-auto p-4">
      <h2 className="text-xl font-semibold mb-4">Campaign Preview</h2>
      
      <div className="space-y-4">
        <section className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-medium text-gray-700 mb-2">Headlines</h3>
          {data.headlines.map((headline, index) => (
            <div key={index} className="bg-white p-2 rounded border mb-2">
              {headline}
            </div>
          ))}
        </section>

        <section className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-medium text-gray-700 mb-2">Description</h3>
          <div className="bg-white p-2 rounded border">
            {data.description}
          </div>
        </section>

        <section className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-medium text-gray-700 mb-2">Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {data.keywords.map((keyword, index) => (
              <span
                key={index}
                className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
              >
                {keyword}
              </span>
            ))}
          </div>
        </section>

        <Button
          onClick={data.onCreateCampaign}
          className="w-full"
          variant="success"
        >
          Create Campaign
        </Button>
      </div>
    </div>
  );
};

export default CampaignPreview;