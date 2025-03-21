
    export type RemoteKeys = 'remote/Button' | 'remote/Header';
    type PackageType<T> = T extends 'remote/Header' ? typeof import('remote/Header') :T extends 'remote/Button' ? typeof import('remote/Button') :any;