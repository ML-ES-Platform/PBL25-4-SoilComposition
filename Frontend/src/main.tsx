import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './chart-setup.ts';

const root = createRoot(document.getElementById('root') as HTMLElement);
root.render(<App />);