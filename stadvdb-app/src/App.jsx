import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import OrdersAnalytics from './assets/pages/Orders.jsx';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/Orders" element={<OrdersAnalytics/>} />
          <Route path="/" element={<Navigate to="/Orders" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;