import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import ChatInput from './components/ChatInput';
import { MessageSquare } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fungsi sementara untuk handle pengiriman pesan
  const handleSendMessage = async (text) => {
    // Nanti di sini kita pasang Axios untuk nembak API FastAPI kamu
    console.log("Pesan terkirim:", text);
  };

  return (
    <div className="flex h-screen bg-nakama-light font-sans text-gray-800">
      {/* Komponen Sidebar di Kiri */}
      <Sidebar />

      {/* Area Utama di Kanan */}
      <div className="flex-1 flex flex-col relative">
        {/* Header Sederhana */}
        <header className="bg-white border-b px-6 py-4 flex items-center shadow-sm z-10">
          <MessageSquare className="text-nakama-primary mr-3" />
          <h1 className="text-xl font-bold text-nakama-dark">Nakama AI Assistant</h1>
        </header>

        {/* Komponen Area Chat (tengah) */}
        <ChatArea messages={messages} isLoading={isLoading} />

        {/* Komponen Input (bawah) */}
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}

export default App;