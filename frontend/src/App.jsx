import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import PublicPayPage from './pages/PublicPayPage';

function App() {
  return (
    <Routes>
      {/* Merchant Dashboard - Requires Auth (Auth logic could be added here later) */}
      <Route path="/" element={<DashboardPage />} />
      
      {/* Public Payment Link UX - No Auth Required */}
      <Route path="/pay/:slug" element={<PublicPayPage />} />
      
      {/* Catch all redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
