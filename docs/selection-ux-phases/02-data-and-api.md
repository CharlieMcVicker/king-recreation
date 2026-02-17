# Task 2: Frontend Data Layer & API

## Description

Expose the validated roots data to the frontend and provide a mechanism to update user selections.

## Steps

1.  **Modify `root-based-dict/src/lib/data.ts`**:
    - Implement `getValidatedRootsRows()`: Read `artifacts/corpora/validated_reconstructable_roots.csv` using `Papa.parse`.
    - Implement `updateUserSelection(corpusId: number, rowIndex: number)`: Use `fs` to read, update the `user_selected` column, and write back the CSV. Ensure only one 'x' exists per `corpus_id`.
2.  **Create `root-based-dict/src/app/api/select-roots/route.ts`**:
    - Implement a `POST` handler that calls `updateUserSelection`.
    - Handle errors gracefully and return success status.
3.  **Verification**:
    - Test the API endpoint using `curl` or a tool like Postman to ensure it correctly modifies the CSV.
