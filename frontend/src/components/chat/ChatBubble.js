// components/Chat/ChatBubble.js
import React from 'react';
import { motion } from 'framer-motion';

const ChatBubble = ({ type, content }) => {
  const isUser = type === 'user';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={`max-w-[70%] p-4 rounded-lg ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-white shadow-sm'
        }`}
      >
        {content}
      </div>
    </motion.div>
  );
};

export default ChatBubble;