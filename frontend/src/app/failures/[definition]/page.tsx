import { analyzeDefinition } from "@/lib/analysis";
import { ArrowLeft, Check, X, AlertTriangle, Bug } from "lucide-react";
import Link from "next/link";

interface Props {
  params: Promise<{ definition: string }>;
}

export default async function FailureDetailPage({ params }: Props) {
  const { definition } = await params;
  const decodedDefinition = decodeURIComponent(definition);
  let analysis;

  try {
    analysis = await analyzeDefinition(decodedDefinition);
  } catch (e) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-800 p-4 rounded-lg">
          Error analyzing definition: {(e as Error).message}
        </div>
        <Link href="/failures" className="mt-4 inline-block text-indigo-600">
          &larr; Back to Failures
        </Link>
      </div>
    );
  }

  const { forms, configurations } = analysis;

  return (
    <div className="space-y-6 pb-20">
      <div className="flex flex-col gap-2">
        <Link
          href="/failures"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to list
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 break-words">
          {decodedDefinition}
        </h1>
        <div className="flex flex-wrap gap-2 text-xs font-mono">
           {Object.entries(forms).map(([key, val]) => (
             <div key={key} className="bg-gray-100 dark:bg-zinc-800 px-2 py-1 rounded">
               <span className="text-gray-500">{key}:</span> <span className="font-semibold text-gray-900 dark:text-gray-100">{val as string}</span>
             </div>
           ))}
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Bug className="w-5 h-5 text-indigo-600" />
          Analysis Results
        </h2>
        
        {configurations.map((config: any, idx: number) => (
          <div 
            key={idx}
            className={`border rounded-lg overflow-hidden ${
              config.outcome === "Success" 
                ? "border-green-200 bg-green-50/30 dark:border-green-900/50 dark:bg-green-900/10" 
                : config.outcome === "Inconsistent"
                  ? "border-amber-200 bg-amber-50/30 dark:border-amber-900/50 dark:bg-amber-900/10"
                  : "border-red-200 bg-red-50/30 dark:border-red-900/50 dark:bg-red-900/10"
            }`}
          >
            <details className="group">
              <summary className="flex items-center justify-between p-4 cursor-pointer select-none">
                <div className="space-y-1">
                   <div className="flex items-center gap-2">
                     {config.outcome === "Success" && <Check className="w-4 h-4 text-green-600" />}
                     {config.outcome === "Inconsistent" && <AlertTriangle className="w-4 h-4 text-amber-600" />}
                     {config.outcome === "Form Failure" && <X className="w-4 h-4 text-red-600" />}
                     <span className={`font-semibold text-sm ${
                        config.outcome === "Success" ? "text-green-700 dark:text-green-300" :
                        config.outcome === "Inconsistent" ? "text-amber-700 dark:text-amber-300" :
                        "text-red-700 dark:text-red-300"
                     }`}>
                       {config.outcome}
                     </span>
                   </div>
                   <div className="text-xs text-gray-500 dark:text-gray-400 flex flex-wrap gap-x-3">
                      <span>{config.config.set_type}</span>
                      <span>{config.config.imp_type}</span>
                      <span>T:{config.config.translocutive ? 'Y' : 'N'}</span>
                      <span>P:{config.config.partitive ? 'Y' : 'N'}</span>
                      <span>D:{config.config.distributive ? 'Y' : 'N'}</span>
                   </div>
                </div>
                <div className="text-gray-400 group-open:rotate-180 transition-transform">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </summary>
              
              <div className="p-4 border-t border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-sm">
                
                {config.outcome === "Form Failure" && (
                  <div className="mb-4">
                    <h4 className="text-xs font-bold text-red-600 uppercase tracking-wide mb-2">Failed Forms</h4>
                    <div className="flex flex-wrap gap-2">
                      {config.failed_forms.map((f: string) => (
                        <span key={f} className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 px-2 py-0.5 rounded text-xs">
                          {f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-2">Possible Stems derived per form</h4>
                <div className="grid gap-2 sm:grid-cols-2">
                   {Object.entries(config.possible_stems).map(([fn, stems]: [string, any]) => (
                     <div key={fn} className="flex flex-col border-b border-gray-100 dark:border-zinc-800 pb-2 last:border-0 sm:border-0">
                        <span className="text-xs text-gray-400 mb-1">{fn}</span>
                        {stems.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                             {stems.map((stem: string, i: number) => (
                               <code key={i} className={`px-1.5 py-0.5 rounded text-xs font-mono ${
                                 config.consistent_stems && config.consistent_stems[fn]?.includes(stem)
                                  ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-900"
                                  : "bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-gray-300"
                               }`}>
                                 -{stem}
                               </code>
                             ))}
                          </div>
                        ) : (
                          <span className="text-xs text-red-400 italic">No stems derived</span>
                        )}
                     </div>
                   ))}
                </div>
              </div>
            </details>
          </div>
        ))}
      </div>
    </div>
  );
}
