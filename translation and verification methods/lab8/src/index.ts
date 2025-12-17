
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

export class FunnyWarning {
    constructor(
        public readonly message: string,
        public readonly code: string, 
        public readonly startLine?: number, 
        public readonly startCol?:number, 
        public readonly endCol?:number, 
        public readonly endLine?: number)
    {
    }
}

export * from './parser';
export * from './funny';
