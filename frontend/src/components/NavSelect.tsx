'use client';

import { useRouter, useSearchParams } from 'next/navigation';

interface SelectProps {
  name: string;
  defaultValue?: string;
  options: { label: string; value: string }[];
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
  otherParams = {}
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
      defaultValue={defaultValue}
      onChange={handleChange}
      className={className}
    >
      {placeholder && <option value="" disabled>{placeholder}</option>}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
