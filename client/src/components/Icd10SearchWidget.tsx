import React, { useState, useEffect } from 'react';

export default function Icd10SearchWidget({ onSelectCode }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }

    const fetchCodes = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/encounters/icd10/search?q=${encodeURIComponent(query)}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setResults(data);
          setIsOpen(data.length > 0);
        }
      } catch (err) {
        console.error('ICD-10 fetch error:', err);
      }
    };

    const handler = setTimeout(fetchCodes, 300);
    return () => clearTimeout(handler);
  }, [query]);

  return (
    <div className="relative">
      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
        Quick ICD-10 Diagnosis Code Search
      </label>
      <input
        type="text"
        className="block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
        placeholder="Type symptom or code (e.g. 'back pain', 'J06')..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => query.trim().length >= 2 && setIsOpen(true)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)} // delay allows click to fire
      />

      {isOpen && (
        <ul className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
          {results.map((item) => (
            <li
              key={item.code}
              onClick={() => {
                onSelectCode(item);
                setQuery('');
                setResults([]);
              }}
              className="cursor-pointer px-4 py-2 text-sm hover:bg-slate-50 flex items-center justify-between"
            >
              <span className="font-semibold text-blue-900 bg-blue-50 px-2 py-0.5 rounded text-xs border border-blue-200">
                {item.code}
              </span>
              <span className="text-slate-700 ml-3 text-xs truncate flex-1 text-right">
                {item.description}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
