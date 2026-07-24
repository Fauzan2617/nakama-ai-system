import React, { useState } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import ChatInput from './components/ChatInput';
import { Sparkles } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState([
  { 
    sender: 'ai', 
    text: 'Halo! Saya adalah Nakama AI. Asisten andalan yang siap membantu pekerjaan tim Nakama hari ini. Ada yang ingin dicari atau didiskusikan?' 
  }
]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async (text) => {
    // 1. Tampilkan pesan user ke UI
    const userMsg = { sender: 'user', text: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // 2. Kirim pesan ke API FastAPI
      const response = await axios.post('http://127.0.0.1:8000/api/rag/chat', {
        message: text
      });

      // 3. Tampilkan balasan AI ke UI
      const aiMsg = { sender: 'ai', text: response.data.response };
      setMessages((prev) => [...prev, aiMsg]);
      
    } catch (error) {
      console.error("API Error:", error);
      const errorMsg = { sender: 'ai', text: 'Maaf, terjadi kesalahan koneksi ke server.' };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white font-sans text-gray-800 selection:bg-blue-200">
      <Sidebar />
      
      <div className="flex-1 flex flex-col relative w-full overflow-hidden">
        <header className="bg-white border-b px-6 py-4 flex items-center justify-between shadow-sm z-10">
          <div className="flex items-center gap-3">
            <div className="bg-nakama-primary/10 p-2 rounded-lg">
              <Sparkles className="text-nakama-primary" size={20} />
            </div>
            <h1 className="text-xl font-bold text-nakama-dark tracking-tight">Nakama AI Assistant</h1>
          </div>
          <div className="text-xs font-semibold bg-blue-50 text-blue-600 border border-blue-200 px-3 py-1.5 rounded-full">
            Beta Version
          </div>
        </header>

        <ChatArea messages={messages} isLoading={isLoading} />
        
        <div className="bg-slate-50">
          <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}

export default App;