
    export type RemoteKeys = 'REMOTE_ALIAS_IDENTIFIER/Button' | 'REMOTE_ALIAS_IDENTIFIER/Header';
    type PackageType<T> = T extends 'REMOTE_ALIAS_IDENTIFIER/Header' ? typeof import('REMOTE_ALIAS_IDENTIFIER/Header') :T extends 'REMOTE_ALIAS_IDENTIFIER/Button' ? typeof import('REMOTE_ALIAS_IDENTIFIER/Button') :any;