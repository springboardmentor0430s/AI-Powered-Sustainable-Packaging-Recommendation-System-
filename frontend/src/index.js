import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './app';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

import { GoogleOAuthProvider } from '@react-oauth/google';

<GoogleOAuthProvider clientId="17542443360-tk7esbse466phnfg781kcuks9roj973o.apps.googleusercontent.com">
  <App />
</GoogleOAuthProvider>
