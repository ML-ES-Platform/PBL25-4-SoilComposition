import Header from './components/Header.tsx';
import Body from './components/Body.tsx';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="app-container">
      <Header />
      <Body />
    </div>
  );
};

export default App;