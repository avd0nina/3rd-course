import { parseFunny } from '../src';
import { testFilesInFolder } from './testFilesInFolder';
export const sampleDir = "./lab08/samples";


describe('08. Testing the sample files', () => {
    testFilesInFolder(sampleDir, parseFunny);
});
