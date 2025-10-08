import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import OrdersAnalytics from './assets/pages/Orders.jsx';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/Orders" element={<OrdersAnalytics/>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;