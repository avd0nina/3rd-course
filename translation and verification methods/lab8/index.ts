
export class FunnyError extends Error {
    constructor(
        message: string,
        public readonly code: string, 
        public readonly startLine?: number, 
        public readonly startCol?:number, 
        public readonly endCol?:number, 
        public readonly endLine?: number)
    {
        super(message);
    }
}

export * from './parser';
export * from './funny';
