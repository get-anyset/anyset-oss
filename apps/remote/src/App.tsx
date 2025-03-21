import React from 'react';
import Button from './components/Button';
import Header from './components/Header';

function App() {
  return (
    <div className="app-container">
      <Header title="Microfrontend Remote Application" />
      
      <h2>Remote App</h2>
      <p>This is the remote application that exposes components for the host to consume.</p>
      
      <Button label="Default Button" onClick={() => alert('Button in remote app clicked!')} />
    </div>
  );
}

export default App; 