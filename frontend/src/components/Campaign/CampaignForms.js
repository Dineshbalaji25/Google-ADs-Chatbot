// components/Campaign/CampaignForm.js
import React from 'react';
import Button from '../common/Button';

const CampaignForm = ({ data, onSubmit, onEdit }) => {
  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-4">Campaign Details</h3>
      <form onSubmit={onSubmit} className="space-y-4">
        {/* Form fields will be added based on campaign requirements */}
        <Button type="submit">Save Campaign</Button>
      </form>
    </div>
  );
};

export default CampaignForm;