import React from "react";
import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children }) {
    const token = localStorage.getItem("token");

    if (!token) {
        // If no token, redirect to login
        return <Navigate to="/login" replace />;
    }

    // If token exists, render the protected component
    return children;
}
