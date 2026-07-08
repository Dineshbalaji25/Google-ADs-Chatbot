// components/common/Loading.js
import React from 'react';
import { Activity } from 'lucide-react';

const Loading = () => {
  return (
    <div className="flex items-center gap-2 text-gray-500 p-4">
      <Activity className="w-4 h-4 animate-spin" />
      <span>Thinking...</span>
    </div>
  );
};

export default Loading;