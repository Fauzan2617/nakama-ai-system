import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { MessageSquare, Plus, History } from 'lucide-react';

const Sidebar = () => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/rag/history');
      setHistory(response.data);
    } catch (error) {
      console.error("Gagal mengambil riwayat:", error);
    }
  };

  return (
    <div className="w-64 bg-nakama-dark text-white flex flex-col h-full border-r border-gray-800 shadow-xl hidden md:flex">
      <div className="p-4">
        <button className="w-full flex items-center justify-center gap-2 bg-nakama-primary hover:bg-blue-600 text-white py-3 px-4 rounded-xl transition-all duration-200 font-semibold shadow-md active:scale-95">
          <Plus size={20} />
          Chat Baru
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2 flex items-center gap-2 mt-4">
          <History size={14} /> Riwayat
        </h3>
        {history.length === 0 ? (
          <p className="text-sm text-gray-500 px-2 italic">Belum ada riwayat percakapan.</p>
        ) : (
          history.slice().reverse().map((item, index) => (
            <button 
              key={index} 
              className="w-full text-left flex items-center gap-3 px-3 py-3 hover:bg-slate-800 rounded-xl transition-colors duration-200 group"
            >
              <MessageSquare size={16} className="text-gray-400 group-hover:text-white transition-colors shrink-0" />
              <div className="truncate text-sm text-gray-300 group-hover:text-white">
                {item.user_message}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
};

export default Sidebar;