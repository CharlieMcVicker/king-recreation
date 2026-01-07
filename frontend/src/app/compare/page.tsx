import { getClasses, getMatches } from "@/lib/data";
import { 
  GitCompare, 
  ArrowRightLeft, 
  CheckCircle, 
  PlusCircle, 
  MinusCircle,
  HelpCircle
} from "lucide-react";
import Link from "next/link";
import NavSelect from "@/components/NavSelect";

export const dynamic = "force-dynamic";

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ classA?: string; classB?: string }>;
}) {
  const params = await searchParams;
  const classes = await getClasses();
  const allMatches = await getMatches();

  const classA = params.classA;
  const classB = params.classB;

  // Helper to get Best Match Scope (Full > Ending > None)
  const getBestScope = (className: string, definition: string) => {
    const classMatches = allMatches.filter((m: any) => 
      m.class === className && 
      m.strictness === "strict" && 
      m.definition === definition &&
      (m.scope === "full" || m.scope === "ending")
    );
    
    if (classMatches.some((m: any) => m.scope === "full")) return "full";
    if (classMatches.some((m: any) => m.scope === "ending")) return "ending";
    return "none";
  };

  // Get all unique definitions involved in either class
  const definitions = new Set<string>();
  if (classA) {
    allMatches
      .filter((m: any) => m.class === classA && m.strictness === "strict" && (m.scope === "full" || m.scope === "ending"))
      .forEach((m: any) => definitions.add(m.definition));
  }
  if (classB) {
    allMatches
      .filter((m: any) => m.class === classB && m.strictness === "strict" && (m.scope === "full" || m.scope === "ending"))
      .forEach((m: any) => definitions.add(m.definition));
  }

  // Buckets
  const fullyShared: string[] = [];
  const fullA: string[] = [];      // Col 1
  const endingA: string[] = [];    // Col 2
  const sharedEnding: string[] = []; // Col 3
  const endingB: string[] = [];    // Col 4
  const fullB: string[] = [];      // Col 5

  definitions.forEach(def => {
    const scopeA = classA ? getBestScope(classA, def) : "none";
    const scopeB = classB ? getBestScope(classB, def) : "none";

    if (scopeA === "full" && scopeB === "full") {
      fullyShared.push(def);
    } else if (scopeA === "full") {
      // Matches A Full, B is Ending or None (but not Full)
      fullA.push(def);
    } else if (scopeB === "full") {
      // Matches B Full, A is Ending or None (but not Full)
      fullB.push(def); 
    } else if (scopeA === "ending" && scopeB === "ending") {
      sharedEnding.push(def);
    } else if (scopeA === "ending") {
      endingA.push(def);
    } else if (scopeB === "ending") {
      endingB.push(def);
    }
  });

  return (
    <div className="flex flex-col h-full gap-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Comparison Tool</h2>
        <p className="text-gray-500 dark:text-zinc-400">Analyze the overlap and unique reach of different verb classes.</p>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase text-gray-400 tracking-wider">Class A</label>
          <NavSelect 
            name="classA" 
            defaultValue={classA || ""}
            placeholder="Select Class A..."
            options={classes.map((c: any) => ({ label: c.class, value: c.class }))}
            otherParams={{ classB: classB || "" }}
            className="w-full bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase text-gray-400 tracking-wider">Class B</label>
          <NavSelect 
            name="classB" 
            defaultValue={classB || ""}
            placeholder="Select Class B..."
            options={classes.map((c: any) => ({ label: c.class, value: c.class }))}
            otherParams={{ classA: classA || "" }}
            className="w-full bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {(!classA || !classB) ? (
        <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-2xl bg-gray-50/50 dark:bg-zinc-900/20 p-12 text-center">
          <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-full text-indigo-600 dark:text-indigo-400 mb-4">
            <GitCompare className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-semibold">Select Two Classes</h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400 max-w-xs mx-auto mt-2">
            Choose two different classes from the dropdowns above to see how their matched verb sets overlap.
          </p>
        </div>
      ) : (
        <div className="space-y-12">
          
          {/* Main 5-Column Grid */}
          <div className="space-y-4">
             <div className="flex items-center gap-2">
                <ArrowRightLeft className="w-5 h-5 text-gray-400" />
                <h3 className="text-lg font-bold">Detailed Comparison</h3>
             </div>
             
             <div className="overflow-x-auto pb-4">
               <div className="min-w-[1200px] grid grid-cols-5 gap-4">
                 
                 {/* 1. Full A */}
                 <div className="space-y-3">
                   <div className="px-2 py-1 border-b-2 border-blue-500">
                     <h4 className="font-bold text-sm text-blue-600 dark:text-blue-400 truncate">Full {classA}</h4>
                     <span className="text-xs text-gray-400">{fullA.length} unique</span>
                   </div>
                   <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 h-[600px] overflow-auto divide-y divide-gray-100 dark:divide-zinc-800">
                      {fullA.map((def, i) => (
                        <div key={i} className="px-3 py-2 text-xs hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-colors">
                          {def}
                        </div>
                      ))}
                   </div>
                 </div>

                 {/* 2. Ending A Only */}
                 <div className="space-y-3">
                    <div className="px-2 py-1 border-b-2 border-sky-400 border-dashed">
                     <h4 className="font-bold text-sm text-sky-500 dark:text-sky-400 truncate text-opacity-80">Ending {classA}</h4>
                     <span className="text-xs text-gray-400">{endingA.length} unique</span>
                   </div>
                   <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 h-[600px] overflow-auto divide-y divide-gray-100 dark:divide-zinc-800">
                      {endingA.map((def, i) => (
                        <div key={i} className="px-3 py-2 text-xs hover:bg-sky-50 dark:hover:bg-sky-900/10 transition-colors">
                          {def}
                        </div>
                      ))}
                   </div>
                 </div>

                 {/* 3. Ending Shared */}
                 <div className="space-y-3">
                   <div className="px-2 py-1 border-b-2 border-purple-500 border-dotted">
                     <h4 className="font-bold text-sm text-purple-600 dark:text-purple-400 truncate text-center">Shared Ending</h4>
                     <div className="text-center"><span className="text-xs text-gray-400">{sharedEnding.length} shared</span></div>
                   </div>
                   <div className="bg-white dark:bg-zinc-900 rounded-xl border border-purple-200 dark:border-purple-800 border-dashed h-[600px] overflow-auto divide-y divide-gray-100 dark:divide-zinc-800 bg-purple-50/30 dark:bg-purple-900/10">
                      {sharedEnding.map((def, i) => (
                        <div key={i} className="px-3 py-2 text-xs hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors font-medium text-purple-700 dark:text-purple-300">
                          {def}
                        </div>
                      ))}
                   </div>
                 </div>

                 {/* 4. Ending B Only */}
                 <div className="space-y-3">
                    <div className="px-2 py-1 border-b-2 border-emerald-400 border-dashed text-right">
                     <h4 className="font-bold text-sm text-emerald-500 dark:text-emerald-400 truncate text-opacity-80">Ending {classB}</h4>
                     <span className="text-xs text-gray-400">{endingB.length} unique</span>
                   </div>
                   <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 h-[600px] overflow-auto divide-y divide-gray-100 dark:divide-zinc-800">
                      {endingB.map((def, i) => (
                        <div key={i} className="px-3 py-2 text-xs hover:bg-emerald-50 dark:hover:bg-emerald-900/10 transition-colors text-right">
                          {def}
                        </div>
                      ))}
                   </div>
                 </div>

                 {/* 5. Full B */}
                 <div className="space-y-3">
                   <div className="px-2 py-1 border-b-2 border-emerald-500 text-right">
                     <h4 className="font-bold text-sm text-emerald-600 dark:text-emerald-400 truncate">Full {classB}</h4>
                     <span className="text-xs text-gray-400">{fullB.length} unique</span>
                   </div>
                   <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 h-[600px] overflow-auto divide-y divide-gray-100 dark:divide-zinc-800">
                      {fullB.map((def, i) => (
                        <div key={i} className="px-3 py-2 text-xs hover:bg-emerald-50 dark:hover:bg-emerald-900/10 transition-colors text-right">
                          {def}
                        </div>
                      ))}
                   </div>
                 </div>

               </div>
             </div>
          </div>

          {/* Fully Shared Section */}
          <div className="bg-white dark:bg-zinc-900 p-8 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">
                  <CheckCircle className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-xl font-bold">Fully Shared Verbs</h3>
                  <p className="text-sm text-gray-500">Matched completely by both {classA} and {classB}</p>
                </div>
              </div>
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                {fullyShared.length}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {fullyShared.map((def, i) => (
                 <div key={i} className="px-3 py-2 text-sm bg-gray-50 dark:bg-zinc-800/50 rounded border border-gray-100 dark:border-zinc-800">
                   {def}
                 </div>
              ))}
              {fullyShared.length === 0 && (
                <div className="col-span-full py-8 text-center text-gray-400 italic">
                  No fully shared verbs found.
                </div>
              )}
            </div>
          </div>
          
        </div>
      )}
    </div>
  );
}
