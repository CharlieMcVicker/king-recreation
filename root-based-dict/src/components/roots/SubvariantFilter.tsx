"use client";

interface SubvariantFilterProps {
  options: string[];
  selected: string;
  onChange: (value: string) => void;
}

export default function SubvariantFilter({
  options,
  selected,
  onChange,
}: SubvariantFilterProps) {
  return (
    <div className="flex items-center gap-3 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-lg px-3 py-2 shadow-sm">
      <label
        htmlFor="variant-select"
        className="text-sm font-medium text-gray-700 dark:text-zinc-300"
      >
        Endings:
      </label>
      <select
        id="variant-select"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        className="text-sm bg-transparent border-none focus:ring-0 cursor-pointer text-indigo-600 dark:text-indigo-400 font-semibold"
      >
        <option value="All">All endings</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}
