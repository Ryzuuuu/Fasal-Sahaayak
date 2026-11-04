import { useEffect, useRef, useState } from 'react';
import { analyzeFarm, getOptions } from './api';
import { ChatPanel } from './components/ChatPanel';
import { FarmForm } from './components/FarmForm';
import { Report } from './components/Report';
import { LANGUAGES, translations } from './i18n/translations';

const ERROR_MESSAGE_KEYS = {
  rate_limited: 'errorRateLimited',
  invalid: 'errorInvalid',
};

export default function App() {
  const [language, setLanguage] = useState('en');
  const [options, setOptions] = useState(null);
  const [report, setReport] = useState(null);
  const [submittedFarm, setSubmittedFarm] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorKey, setErrorKey] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const reportRef = useRef(null);
  const t = translations[language];

  useEffect(() => {
    getOptions().then(setOptions).catch(() => setErrorKey('errorNetwork'));
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    document.title = t.appName;
  }, [language, t.appName]);

  useEffect(() => {
    if (report) reportRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [report]);

  const handleSubmit = async (farm) => {
    setIsLoading(true);
    setErrorKey(null);
    setFieldErrors({});
    try {
      setReport(await analyzeFarm(farm));
      setSubmittedFarm(farm);
    } catch (error) {
      setErrorKey(ERROR_MESSAGE_KEYS[error.kind] ?? 'errorNetwork');
      setFieldErrors(Object.fromEntries((error.fields ?? []).map(({ field }) => [field, true])));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="bg-emerald-800 text-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div>
            <h1 className="text-2xl font-bold">{t.appName}</h1>
            <p className="text-sm text-emerald-100">{t.tagline}</p>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <span>{t.language}</span>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="rounded-lg bg-white px-2 py-1 text-stone-900 focus:outline-none focus:ring-2 focus:ring-emerald-200"
            >
              {Object.entries(LANGUAGES).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <main className="min-w-0 space-y-6">
          {options && (
            <FarmForm
              t={t}
              options={options}
              isLoading={isLoading}
              fieldErrors={fieldErrors}
              onSubmit={handleSubmit}
            />
          )}
          {errorKey && (
            <p role="alert" className="rounded-lg bg-red-50 p-4 text-red-800">
              {t[errorKey]}
            </p>
          )}
          <div ref={reportRef} className="scroll-mt-4">
            {report ? (
              <Report t={t} report={report} />
            ) : (
              options && (
                <p className="rounded-2xl bg-stone-100 p-6 text-center text-stone-600">
                  {t.emptyReport}
                </p>
              )
            )}
          </div>
          <footer className="text-sm text-stone-500">{t.disclaimer}</footer>
        </main>

        {options && (
          <ChatPanel
            t={t}
            language={language}
            farm={submittedFarm}
            aiEnabled={options.ai_chat_enabled}
          />
        )}
      </div>
    </div>
  );
}
