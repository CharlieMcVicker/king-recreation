'use client';

import { useState } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  ArrowRight,
  Info
} from "lucide-react";

interface Match {
  definition: string;
  class: string;
  strictness: string;
  scope: string;
  stem_final_match_present: string;
  stem_final_match_imperfective: string;
  stem_final_match_perfective: string;
  stem_final_match_imperative: string;
  stem_final_match_infinitive: string;
}

interface MatchExplorerProps {
  matches: Match[];
  classPattern: any;
}

export default function MatchExplorer({ matches, classPattern }: MatchExplorerProps) {
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(matches[0] || null);

  const forms = [
    { key: 'present', label: 'Present' },
    { key: 'imperfective', label: 'Imperfective' },
    { key: 'perfective', label: 'Perfective' },
    { key: 'imperative', label: 'Imperative' },
    { key: 'infinitive', label: 'Infinitive' }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-[600px]">
      {/* Scrollable List */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm flex flex-col h-full overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 flex items-center justify-between">
          <h3 className="font-semibold text-sm">Verbs ({matches.length})</h3>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-zinc-800">
          {matches.map((match, i) => (
            <button
              key={`${match.definition}-${i}`}
              onClick={() => setSelectedMatch(match)}
              className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors ${
                selectedMatch?.definition === match.definition ? 'bg-indigo-50/50 dark:bg-indigo-900/10 border-r-2 border-indigo-500' : ''
              }`}
            >
              <span className="text-sm font-medium">{match.definition}</span>
              <ArrowRight className={`w-4 h-4 transition-transform ${selectedMatch?.definition === match.definition ? 'translate-x-1 text-indigo-500' : 'text-gray-300'}`} />
            </button>
          ))}
          {matches.length === 0 && (
            <div className="p-8 text-center text-gray-400 text-sm italic">
              No matches found.
            </div>
          )}
        </div>
      </div>

      {/* Detail View */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm flex flex-col h-full overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20">
          <h3 className="font-semibold text-sm">Match Details</h3>
        </div>
        
        {selectedMatch ? (
          <div className="p-6 space-y-8 flex-1 overflow-y-auto">
            <div>
              <h4 className="text-lg font-bold mb-1">{selectedMatch.definition}</h4>
              <div className="flex gap-2">
                <span className="text-[10px] bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                  {selectedMatch.strictness}
                </span>
                <span className="text-[10px] bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                  {selectedMatch.scope} scope
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <h5 className="text-[10px] font-bold uppercase text-gray-400 tracking-wider">Form-level Match Results</h5>
              <div className="space-y-3">
                {forms.map(form => {
                  const isMatch = selectedMatch[`stem_final_match_${form.key}` as keyof Match] === 'True';
                  return (
                    <div key={form.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-zinc-950 rounded border border-gray-100 dark:border-zinc-800">
                      <div className="flex flex-col">
                        <span className="text-xs font-semibold capitalize">{form.label}</span>
                        <span className="text-[10px] font-mono text-gray-400">Pattern: {classPattern[form.key] || '-'}</span>
                      </div>
                      {isMatch ? (
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="p-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-900/20 rounded-lg">
              <div className="flex gap-3">
                <Info className="w-5 h-5 text-amber-500 shrink-0" />
                <div className="text-xs text-amber-800 dark:text-amber-200 leading-relaxed">
                  <strong>Stem Final Rule:</strong> For a "full" match, all five forms must match the class pattern at the stem-final boundary. If any form shows an <XCircle className="w-3 h-3 inline pb-0.5" />, the match scope is limited to "ending".
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-gray-400">
            <Info className="w-12 h-12 mb-4 opacity-20" />
            <p className="text-sm italic">Select a verb to see detailed matching results.</p>
          </div>
        )}
      </div>
    </div>
  );
}
