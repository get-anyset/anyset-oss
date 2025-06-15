import React from 'react';

export interface DummyComponentProps {
  title?: string;
}

export const DummyComponent: React.FC<DummyComponentProps> = ({ title = 'Dummy Component' }) => {
  return (
    <div>
      <h1>{title}</h1>
      <p>This is a dummy component for testing purposes.</p>
    </div>
  );
};
