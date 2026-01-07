import { describe, it, expect, vi } from 'vitest';
import { readCsv } from './data';
import fs from 'fs';

vi.mock('fs');

describe('readCsv', () => {
  it('parses CSV content correctly', async () => {
    const mockCsv = 'col1,col2\nval1,val2\nval3,val4';
    vi.spyOn(fs, 'readFileSync').mockReturnValue(mockCsv as any);

    const result = await readCsv('dummy', 'test.csv');
    expect(result).toEqual([
      { col1: 'val1', col2: 'val2' },
      { col1: 'val3', col2: 'val4' },
    ]);
  });
});
