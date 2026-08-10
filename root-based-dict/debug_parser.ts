
import fs from 'fs';
import path from 'path';
import Papa from 'papaparse';

const csvPath = path.join(process.cwd(), '../artifacts/matches.csv');
const content = fs.readFileSync(csvPath, 'utf8');

Papa.parse(content, {
  header: true,
  skipEmptyLines: true,
  complete: (results) => {
    const data = results.data as any[];
    const firstMatch = data[0];
    console.log('Keys:', Object.keys(firstMatch));
    console.log('First match values:', firstMatch);
    
    // Check specific columns for whitespace
    const present = firstMatch['stem_final_match_present'];
    console.log(`'${present}' === 'True':`, present === 'True');
    console.log(`Length: ${present.length}`);
    
    // Find a match that might be problematic (if any)
    const problematic = data.find(d => d.scope === 'full');
    console.log('Full match sample:', problematic);
  }
});
