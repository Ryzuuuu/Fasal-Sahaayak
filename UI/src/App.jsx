import React, { useState, useEffect, useRef } from 'react';

// --- Data and API ---
import { translations } from './i18n/translations';
// CHANGED: Cleaned up duplicate imports. This is the only one we need.
import { getAnalysisReport } from './api/analysisService';

// --- Components ---
import { Header } from './components/Header';
import { ChatbotSidebar } from './components/ChatbotSidebar';
import { FarmInputForm } from './components/FarmInputForm';
import { Recommendations } from './components/Recommendations';
import './App.css';

function App() {
  const [lang, setLang] = useState('en');
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState(null);
  const [error, setError] = useState(null); // ADDED: State to manage API errors
  const recommendationsRef = useRef(null);

  const t = translations[lang];

  useEffect(() => {
    if (recommendations && recommendationsRef.current) {
      recommendationsRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [recommendations]);

  // CHANGED: This entire function is updated to call the real API and handle errors.
  const handleGetAdvice = async (formData) => {
    setIsLoading(true);
    setRecommendations(null);
    setError(null); // Clear previous errors

    try {
      // Use the REAL API service function we created
      const recs = await getAnalysisReport(formData);
      setRecommendations(recs);
    } catch (e) {
      // If the API call fails, we catch the error and display it
      setError(e.message);
    } finally {
      // This ensures the loading spinner always stops, even if there's an error
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gray-50 min-h-screen">
      <Header t={t} setLang={setLang} lang={lang} />
      
      <div className="flex">
        

        <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
          <div className="max-w-4xl mx-auto">
            <FarmInputForm t={t} onSubmit={handleGetAdvice} isLoading={isLoading} />
            
            {isLoading && (
              <div className="spinner-container">
                <div className="spinner"></div>
                <p className="text-center text-gray-500 mt-2">{t.loadingText}</p>
              </div>
            )}

            {/* ADDED: A small block to display any errors that occur */}
            {error && (
              <div className="error-message">
                <p><strong>{t.errorTitle}:</strong> {error}</p>
              </div>
            )}
            
            <Recommendations 
              recommendations={recommendations} 
              t={t} 
              elementRef={recommendationsRef} 
            />
          </div>
        </main>
        <ChatbotSidebar t={t} />
      </div>
    </div>
  );
}

export default App;