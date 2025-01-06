import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login';
import Form_Input from './Form_Input'; 

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/" />;
};

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route
          path="/form_input"
          element={
            <PrivateRoute>
              <Form_Input />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
};

export default App;
