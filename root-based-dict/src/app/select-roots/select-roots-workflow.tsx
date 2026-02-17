"use client";

import React from "react";
import { ListTodo } from "lucide-react";

interface SelectRootsWorkflowProps {
  initialData: any[]; // Adjust the type as needed based on getValidatedRootsRows
}

export default function SelectRootsWorkflow({
  initialData,
}: SelectRootsWorkflowProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <ListTodo className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Select Roots
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Select the correct root forms for reconstruction.
          </p>
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {initialData.length} entries loaded
        </div>
      </div>

      <div className="bg-white dark:bg-zinc-900 rounded-lg shadow border border-gray-200 dark:border-zinc-800 p-6">
        <p className="text-gray-500 dark:text-gray-400">
          Workflow component initiated. Ready for implementation.
        </p>
        {/* Placeholder for future implementation */}
        <div className="mt-4 p-4 bg-gray-50 dark:bg-zinc-800 rounded text-xs font-mono overflow-auto max-h-40">
          {JSON.stringify(initialData.slice(0, 3), null, 2)}
        </div>
      </div>
    </div>
  );
}
