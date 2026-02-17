# Task 3: Navigation & Route Setup

## Description

Register the new workflow in the application navigation and create the entry point.

## Steps

1.  **Modify `root-based-dict/src/app/layout.tsx`**:
    - Add a new `Link` to the sidebar navigation.
    - Label: "Select Roots".
    - Icon: Use `CheckSquare` or `ListTodo` from `lucide-react`.
    - Href: `/select-roots`.
2.  **Create `root-based-dict/src/app/select-roots/page.tsx`**:
    - A server component that fetches all roots from `getValidatedRootsRows()`.
    - Passes the data to a (yet to be created) client component `SelectRootsWorkflow`.
3.  **Verification**:
    - Verify the "Select Roots" link appears in the sidebar and navigates to the (currently empty) page.
