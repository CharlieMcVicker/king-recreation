import React from "react";
import { ReconstructableVerb } from "@/lib/data-shared";

interface ConfigFlagsProps {
  config: ReconstructableVerb["config"];
  className?: string;
}

export function ConfigFlags({ config, className = "" }: ConfigFlagsProps) {
  const flags = [
    {
      label: "TR",
      active: config.pre.translocutive,
      title: "Translocutive",
      color: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
    },
    {
      label: "PA",
      active: config.pre.partitive,
      title: "Partitive",
      color:
        "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300",
    },
    {
      label: "DI",
      active: config.pre.distributive,
      title: "Distributive",
      color:
        "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
    },
    {
      label: "3OBJ",
      active: config.pron.use_3rd_person_object,
      title: "3rd Person Object",
      color: "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300",
    },
    {
      label: "KA",
      active: config.pron.use_ka_variant,
      title: "Ka-variant",
      color: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
    },
    {
      label: `SET ${config.pron.set_type.toUpperCase()}`,
      active: true,
      title: `Pronominal Set ${config.pron.set_type.toUpperCase()}`,
      color:
        config.pron.set_type.toLowerCase() === "a"
          ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300"
          : "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300",
    },
  ];

  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {flags
        .filter((f) => f.active)
        .map((f) => (
          <span
            key={f.label}
            title={f.title}
            className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${f.color}`}
          >
            {f.label}
          </span>
        ))}
    </div>
  );
}
