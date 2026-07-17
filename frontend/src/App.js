import React, { useState } from 'react';
import ChatInterface from './components/chat/ChatInterface';
import AuthScreen from './components/common/AuthScreen';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('auth_token'));

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_email');
    sessionStorage.removeItem('chat_session_id'); // clear conversation session on logout
    setIsAuthenticated(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col h-screen">
      {isAuthenticated ? (
        <div className="flex flex-col h-full">
          <header className="bg-white shadow-sm py-3 px-6 flex justify-between items-center border-b shrink-0">
            <h1 className="text-lg font-bold text-gray-800">Google Ads AI Chatbot</h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">{localStorage.getItem('auth_email')}</span>
              <button
                onClick={handleLogout}
                className="text-xs font-semibold text-red-600 hover:text-red-500 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </header>
          <div className="flex-1 min-h-0">
            <ChatInterface />
          </div>
        </div>
      ) : (
        <AuthScreen onAuthSuccess={() => setIsAuthenticated(true)} />
      )}
    </div>
  );
}

export default App;

