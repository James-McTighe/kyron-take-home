import React, { useState } from 'react';

interface Icd10Code {
  code: string;
  description: string;
}

interface SearchProps {
  onSelectCode: (code: Icd10Code) => void;
}

export const Icd10SearchWidget: React.FC<SearchProps> = ({ onSelectCode }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Icd10Code[]>([]);

  const handleSearch = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    if (val.length < 3) return;

    try {
      const res = await fetch(`/api/icd10/search?q=${encodeURIComponent(val)}`);
      const data = await res.json();
      setResults(data.slice(0, 5)); // Limit to top 5 results
    } catch (err) {
      console.error("ICD-10 search error", err);
    }
  };

  return (
    <div className="bg-slate-50 p-4 rounded-md border border-slate-200">
      <h3 className="text-sm font-semibold text-slate-700 mb-2">Semantic ICD-10 Finder</h3>
      <input
        type="text"
        value={query}
        onChange={handleSearch}
        placeholder="Type symptom or condition (e.g., hypertension)..."
        className="w-full px-3 py-2 border text-sm border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-slate-500"
      />
      {results.length > 0 && (
        <ul className="mt-2 bg-white border border-slate-200 rounded divide-y divide-slate-100 shadow-sm max-h-40 overflow-y-auto">
          {results.map((item) => (
            <li 
              key={item.code}
              onClick={() => onSelectCode(item)}
              className="p-2 text-xs hover:bg-slate-100 cursor-pointer text-slate-600 transition-colors"
            >
              <strong className="text-slate-900 font-mono">{item.code}</strong> - {item.description}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
