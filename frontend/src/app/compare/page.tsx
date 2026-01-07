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
  searchParams: { classA?: string; classB?: string };
}) {
  const classes = await getClasses();
  const allMatches = await getMatches();

  const classA = searchParams.classA;
  const classB = searchParams.classB;

  const matchesA = classA 
    ? allMatches.filter((m: any) => m.class === classA && m.scope === "full" && m.strictness === "strict")
    : [];
  const matchesB = classB 
    ? allMatches.filter((m: any) => m.class === classB && m.scope === "full" && m.strictness === "strict")
    : [];

  const defsA = new Set(matchesA.map((m: any) => m.definition));
  const defsB = new Set(matchesB.map((m: any) => m.definition));

  const onlyA = matchesA.filter(m => !defsB.has(m.definition));
  const both = matchesA.filter(m => defsB.has(m.definition));
  const onlyB = matchesB.filter(m => !defsA.has(m.definition));

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
        <div className="space-y-8">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm transition-all hover:shadow-md border-l-4 border-l-blue-500">
               <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Only {classA}</span>
                  <MinusCircle className="w-4 h-4 text-blue-500" />
               </div>
               <div className="text-2xl font-bold">{onlyA.length}</div>
               <p className="text-[10px] text-gray-400 mt-1">Verbs unique to Class A</p>
            </div>
            <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm transition-all hover:shadow-md border-l-4 border-l-purple-500">
               <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Intersection</span>
                  <CheckCircle className="w-4 h-4 text-purple-500" />
               </div>
               <div className="text-2xl font-bold">{both.length}</div>
               <p className="text-[10px] text-gray-400 mt-1">Verbs matched by BOTH</p>
            </div>
            <div className="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-gray-200 dark:border-zinc-800 shadow-sm transition-all hover:shadow-md border-l-4 border-l-emerald-500">
               <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Only {classB}</span>
                  <PlusCircle className="w-4 h-4 text-emerald-500" />
               </div>
               <div className="text-2xl font-bold">{onlyB.length}</div>
               <p className="text-[10px] text-gray-400 mt-1">Verbs unique to Class B</p>
            </div>
          </div>

          {/* Comparison Lists */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Column A */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold flex items-center gap-2 px-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                Unique to {classA}
              </h3>
              <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 h-[500px] overflow-auto divide-y divide-gray-100 dark:divide-zinc-800">
                {onlyA.map((m, i) => (
                  <div key={i} className="px-4 py-3 text-sm hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                    {m.definition}
                  </div>
                ))}
                {onlyA.length === 0 && <div className="p-8 text-center text-gray-400 italic text-xs">No unique results.</div>}
              </div>
            </div>

            {/* Column Both */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold flex items-center gap-2 px-2">
                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                Shared Verbs
              </h3>
              <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 h-[500px] overflow-auto divide-y divide-gray-100 dark:divide-zinc-800">
                {both.map((m, i) => (
                  <div key={i} className="px-4 py-3 text-sm hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                    {m.definition}
                  </div>
                ))}
                {both.length === 0 && <div className="p-8 text-center text-gray-400 italic text-xs">No shared results.</div>}
              </div>
            </div>

            {/* Column B */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold flex items-center gap-2 px-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                Unique to {classB}
              </h3>
              <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 h-[500px] overflow-auto divide-y divide-gray-100 dark:divide-zinc-800">
                {onlyB.map((m, i) => (
                  <div key={i} className="px-4 py-3 text-sm hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                    {m.definition}
                  </div>
                ))}
                {onlyB.length === 0 && <div className="p-8 text-center text-gray-400 italic text-xs">No unique results.</div>}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
