'use client';

import { useState } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  ArrowRight,
  Info,
  BookOpen
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

interface EntryExplorerProps {
  matches: Match[];
  classes: any[];
  corpusEntry: any;
}

export default function EntryExplorer({ matches, classes, corpusEntry }: EntryExplorerProps) {
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(matches[0] || null);

  // Group matches by strictness or just list them? 
  // Let's just list them all, maybe sorted by Class Name.
  // Create a map of class -> index for sorting
  const classOrder = new Map(classes.map((c, i) => [c.class, i]));

  const sortedMatches = [...matches].sort((a, b) => {
    // Sort by Strictness (strict first) then Scope (full first) then Class Order
    if (a.strictness !== b.strictness) return a.strictness === 'strict' ? -1 : 1;
    if (a.scope !== b.scope) return a.scope === 'full' ? -1 : 1;
    
    // Use the index from the classes array
    const orderA = classOrder.get(a.class) ?? 9999;
    const orderB = classOrder.get(b.class) ?? 9999;
    return orderA - orderB;
  });

  const selectedClassData = selectedMatch 
    ? classes.find(c => c.class === selectedMatch.class) 
    : null;

  const forms = [
    { key: 'present', label: 'Present' },
    { key: 'imperfective', label: 'Imperfective' },
    { key: 'perfective', label: 'Perfective' },
    { key: 'imperative', label: 'Imperative' },
    { key: 'infinitive', label: 'Infinitive' }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-[600px]">
      {/* Scrollable List of Matches */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm flex flex-col h-full overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20 flex items-center justify-between">
          <h3 className="font-semibold text-sm">Matched Classes ({matches.length})</h3>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-gray-100 dark:divide-zinc-800">
          {sortedMatches.map((match, i) => (
            <button
              key={`${match.class}-${match.strictness}-${i}`}
              onClick={() => setSelectedMatch(match)}
              className={`w-full text-left px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors ${
                selectedMatch === match ? 'bg-indigo-50/50 dark:bg-indigo-900/10 border-r-2 border-indigo-500' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                   match.scope === 'full' && match.strictness === 'strict' ? 'bg-indigo-500' :
                   match.scope === 'full' ? 'bg-emerald-500' : 
                   'bg-amber-500'
                }`} />
                <div className="flex flex-col gap-0.5">
                   <span className="text-sm font-bold font-mono">{match.class}</span>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                 <div className="flex flex-col items-end gap-1">
                    <span className="text-[10px] uppercase font-bold text-gray-500">{match.strictness}</span>
                    {match.scope === 'ending' && (
                        <span className="text-[10px] uppercase font-bold text-amber-600 bg-amber-50 dark:bg-amber-900/20 px-1.5 py-0.5 rounded">Near Miss</span>
                    )}
                    {match.scope === 'full' && (
                        <span className="text-[10px] uppercase font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-1.5 py-0.5 rounded">Full Match</span>
                    )}
                 </div>
                <ArrowRight className={`w-4 h-4 transition-transform ${selectedMatch === match ? 'translate-x-1 text-indigo-500' : 'text-gray-300'}`} />
              </div>
            </button>
          ))}
          {matches.length === 0 && (
            <div className="p-8 text-center text-gray-400 text-sm italic">
              No matches found for this verb.
            </div>
          )}
        </div>
      </div>

      {/* Detail View */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm flex flex-col h-full overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20">
          <h3 className="font-semibold text-sm">Match Details</h3>
        </div>
        
        {selectedMatch && selectedClassData ? (
          <div className="p-6 space-y-8 flex-1 overflow-y-auto">
            <div>
              <div className="flex items-center gap-2 mb-2">
                 <BookOpen className="w-4 h-4 text-indigo-500" />
                 <h4 className="text-lg font-bold font-mono text-indigo-600 dark:text-indigo-400">{selectedMatch.class}</h4>
              </div>
              
              <div className="flex gap-2">
                <span className="text-[10px] bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                  {selectedMatch.strictness}
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                  selectedMatch.scope === 'full' 
                    ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400'
                    : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
                }`}>
                  {selectedMatch.scope === 'full' ? 'Full Match' : 'Near Miss'}
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <h5 className="text-[10px] font-bold uppercase text-gray-400 tracking-wider">Form Verification vs Class Pattern</h5>
              <div className="space-y-3">
                {forms.map(form => {
                  const rawValue = selectedMatch[`stem_final_match_${form.key}` as keyof Match];
                  const isMatch = String(rawValue || '').trim().toLowerCase() === 'true';
                  const actualForm = corpusEntry?.[form.key];
                  const pattern = selectedClassData?.[form.key];

                  return (
                    <div key={form.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-zinc-950 rounded border border-gray-100 dark:border-zinc-800">
                      <div className="flex flex-col gap-1 w-full mr-4">
                        <span className="text-xs font-semibold capitalize text-gray-500">{form.label}</span>
                        <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3">
                           <span className="text-lg font-serif text-gray-800 dark:text-zinc-200 leading-none">
                             {actualForm || '-'}
                           </span>
                           <span className="text-xs text-gray-400 font-mono">
                             (Pattern: <span className="text-indigo-500">{pattern || '-'}</span>)
                           </span>
                        </div>
                      </div>
                      <div className="shrink-0">
                        {isMatch ? (
                            <CheckCircle className="w-6 h-6 text-emerald-500" />
                        ) : (
                            <XCircle className="w-6 h-6 text-red-500" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="p-4 bg-amber-50 dark:bg-amber-900/10 border border-amber-100 dark:border-amber-900/20 rounded-lg">
              <div className="flex gap-3">
                <Info className="w-5 h-5 text-amber-500 shrink-0" />
                <div className="text-xs text-amber-800 dark:text-amber-200 leading-relaxed">
                  <strong>Verification Info:</strong> This view compares the actual forms of <em>{corpusEntry.definition}</em> against the patterns defined in Class <strong>{selectedMatch.class}</strong>.
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-8 flex-1 overflow-y-auto">
             <div>
               <div className="flex items-center gap-2 mb-2">
                 <h4 className="text-lg font-bold font-serif text-gray-900 dark:text-white">Corpus Forms</h4>
               </div>
               <p className="text-xs text-gray-500 dark:text-zinc-400 leading-relaxed">
                 {matches.length === 0 
                    ? "No matches found for this verb. Showing raw corpus forms below."
                    : "Select a matched class from the list to see comparison details."}
               </p>
             </div>

             <div className="space-y-4">
               <h5 className="text-[10px] font-bold uppercase text-gray-400 tracking-wider">Forms</h5>
               <div className="space-y-3">
                 {forms.map(form => {
                   const actualForm = corpusEntry?.[form.key];
                   return (
                     <div key={form.key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-zinc-950 rounded border border-gray-100 dark:border-zinc-800">
                       <div className="flex flex-col gap-1 w-full">
                         <span className="text-xs font-semibold capitalize text-gray-500">{form.label}</span>
                         <span className="text-lg font-serif text-gray-800 dark:text-zinc-200 leading-none">
                           {actualForm || '-'}
                         </span>
                       </div>
                     </div>
                   );
                 })}
               </div>
             </div>
             
             {matches.length > 0 && (
                <div className="p-4 bg-indigo-50 dark:bg-indigo-900/10 border border-indigo-100 dark:border-indigo-900/20 rounded-lg">
                  <div className="flex gap-3">
                    <Info className="w-5 h-5 text-indigo-500 shrink-0" />
                    <div className="text-xs text-indigo-800 dark:text-indigo-200 leading-relaxed">
                      Select a match from the left sidebar to compare these forms against a specific class pattern.
                    </div>
                  </div>
                </div>
             )}
          </div>
        )}
      </div>
    </div>
  );
}
