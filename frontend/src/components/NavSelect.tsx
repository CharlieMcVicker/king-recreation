"use client";

import { useRouter, useSearchParams } from "next/navigation";

interface Option {
  label: string;
  value: string;
}

interface OptionGroup {
  group: string;
  items: Option[];
}

interface SelectProps {
  name: string;
  defaultValue?: string;
  options: (Option | OptionGroup)[];
  placeholder?: string;
  className?: string;
  otherParams?: Record<string, string>;
}

export default function NavSelect({
  name,
  defaultValue,
  options,
  placeholder,
  className,
  otherParams = {},
}: SelectProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    const params = new URLSearchParams(searchParams.toString());
    params.set(name, value);

    // Add other fixed params if needed
    Object.entries(otherParams).forEach(([k, v]) => {
      if (v) params.set(k, v);
    });

    router.push(`?${params.toString()}`);
  };

  return (
    <select
      name={name}
      value={defaultValue} // Using value for controlled feel if possible, or defaultValue
      onChange={handleChange}
      className={className}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((opt, i) => {
        if ("group" in opt) {
          return (
            <optgroup key={opt.group + i} label={opt.group}>
              {opt.items.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </optgroup>
          );
        }
        return (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        );
      })}
    </select>
  );
}
