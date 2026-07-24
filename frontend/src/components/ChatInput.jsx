import React, { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

const ChatInput = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="bg-gradient-to-t from-slate-50 to-transparent p-4 sm:px-6 sm:pb-6">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-end shadow-lg rounded-2xl bg-white border border-gray-200 overflow-hidden focus-within:ring-2 focus-within:ring-nakama-primary/50 transition-all">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tanyakan sesuatu pada Nakama AI..."
          className="w-full resize-none max-h-40 min-h-[60px] p-4 pr-16 bg-transparent focus:outline-none text-[15px]"
          rows={1}
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className="absolute right-3 bottom-3 p-2.5 bg-nakama-primary text-white rounded-xl hover:bg-blue-600 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} className="ml-0.5" />}
        </button>
      </form>
      <div className="text-center mt-3">
        <span className="text-xs text-gray-400 font-medium">Nakama AI dapat membuat kesalahan. Harap periksa kembali informasi penting.</span>
      </div>
    </div>
  );
};

export default ChatInput;