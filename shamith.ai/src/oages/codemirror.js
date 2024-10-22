import React, { useState, useEffect } from 'react';
import './codemirror.css';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { dracula } from '@uiw/codemirror-theme-dracula';
import { useNavigate } from 'react-router-dom';  // Use navigate for routing

function CodeMirrorPage() {
  const [code, setCode] = useState('def solution(nums) -> int:\n pass \n');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [timeLeft, setTimeLeft] = useState(5); // Timer for thinking
  const [canProceed, setCanProceed] = useState(false); // Control Next Stage button visibility
  const navigate = useNavigate();  // Use for navigating to ResultsPage

  // Problem description to display and narrate
  const problemDescription = `You are given a list of integers \`nums\`.
  Your task is to write a function \`solution(nums)\` that returns the sum of all even positive numbers in the list.
  If there are no even positive numbers, return \`0\`.
  The integers can be positive, negative, or zero.
  Only even positive numbers should be included in the sum.`;

  // Test Code function (Submit code to backend)
  const testCode = async () => {
    if (!code) {
      alert("Please enter some code before testing.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:5000/run-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: code,  // Sending the code
          problemId: 1 // Change this based on the problem displayed
        }),
      });

      const data = await response.json();
      setResults(data);  // Store the results from the backend
      setCanProceed(true);  // Enable Next Stage button
    } catch (error) {
      console.error('Error submitting code:', error);
    } finally {
      setLoading(false);  // Stop loading once complete
    }
  };

  const askCode = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:5000/process-voice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: code,  // Sending the code
          problemId: 1 // Change this based on the problem displayed
        }),
      });
    } catch (error) {
      console.error('Error submitting code:', error);
    } finally {
      setLoading(false);  // Stop loading once complete
    }
  };

  // Function to handle "Next Stage" button click
  const goToResults = () => {
    // Navigate to ResultsPage with the results data (raw numbers, scores, etc.)
    navigate('/results', { state: { results: results } });
  };

  return (
    <div className="App">
      <div className="container">
        <div className="question-section">
          <h1>Technical Question</h1>
          <div className="problem-description-box">
            <p>{problemDescription}</p> {/* Problem description displayed in styled box */}
          </div>
        </div>
        <div className="timer-section">
          {thinking ? <p>Thinking time: {timeLeft} seconds left</p> : null}
        </div>
        <div className="editor-section">
          <CodeMirror
            value={code}
            theme={dracula}
            height="300px"
            width="500px"
            extensions={[python()]}
            className="editor"
            onChange={(value) => setCode(value)} // Ensure code updates on typing
            editable={true} // Allow typing
          />
        </div>
        <div className='submitTestButton'>
          <button className="test-button" disabled={loading} onClick={testCode}>
            {loading ? "Testing..." : "Test Code"}
          </button>
          <button className="test-button" disabled={loading} onClick={askCode}>
            {loading ? "Ask..." : "Ask"}
          </button>
        </div>
        
        {results && (
          <div className="results-section">
            <h2>Results</h2>
            <p>Test Cases Passed: {results.passed}/{results.total}</p>
            {results.error && <p>Error: {results.error}</p>}
          </div>
        )}
        {canProceed && (
          <button className="next-stage-button" onClick={goToResults}>
            Next Stage
          </button>
        )}
      </div>
    </div>
  );
}

export default CodeMirrorPage;
