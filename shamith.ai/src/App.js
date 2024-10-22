import './App.css';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LandingPage from './oages/LandingPage';
import CodeMirrorPage from './oages/codemirror';
import ResultsPage from './oages/ResultsPage';
import ResumeQ from './oages/ResumeQ';

function App() {
  return (
    <Router>
        <div className="App">
            <Routes>
                <Route exact path="/" element={<LandingPage />} />    
                <Route path="/ResumeQ" element={<ResumeQ />} />
                <Route path="/codemirror" element={<CodeMirrorPage />} />
                <Route path="/results" element={<ResultsPage />} />
            </Routes>
        </div>
    </Router>
    
  );
}

export default App;
