import React, { lazy, Suspense, useState, useEffect } from 'react';

// Dynamically import the remote components
const RemoteButton = lazy(() => import('remote/Button'));
const RemoteHeader = lazy(() => import('remote/Header'));

// Type definition for data from API
interface Item {
  id: number;
  name: string;
  description: string;
}

function App() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/items')
      .then(response => response.json())
      .then(data => {
        setItems(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching items:', error);
        setLoading(false);
      });
  }, []);

  return (
    <div className="app-container">
      <Suspense fallback={<div>Loading header...</div>}>
        <RemoteHeader title="Microfrontend Host Application" />
      </Suspense>
      
      <div className="content-section">
        <h2>Host Application</h2>
        <p>This is the container application that loads components from the remote app.</p>
        
        <Suspense fallback={<div>Loading button...</div>}>
          <RemoteButton label="Remote Button" onClick={() => alert('Button clicked!')} />
        </Suspense>
      </div>

      <div className="content-section">
        <h2>Items from API</h2>
        {loading ? (
          <p>Loading items...</p>
        ) : (
          <ul>
            {items.map(item => (
              <li key={item.id}>
                <h3>{item.name}</h3>
                <p>{item.description}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default App; 