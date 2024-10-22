import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './ResumeQ.css';

const ResumeQ = () => {
    const [isButtonEnabled, setIsButtonEnabled] = useState(true); // Button starts as disabled
    const [currentQuestion, setCurrentQuestion] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);
    const [questionsList, setQuestionsList] = useState([]);
    const location = useLocation();
    const navigate = useNavigate();
    const questions = location.state?.questions || '';

    useEffect(() => {
        if (questions.length > 0) {
            const parsedQuestions = questions.split(/(?<=\?|\.)\s*\d+\.\s*\*\*?/).map(q => q.trim()).filter(q => q);
            setQuestionsList(parsedQuestions); // Store parsed questions in state
            askNextQuestion(parsedQuestions[0]); // Ask the first question
        }
    }, [questions]);

    const askNextQuestion = async (question) => {
        try {
            // Ask the next question by sending it to the backend
            await fetch('http://127.0.0.1:5000/ask-question', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ question }),
            });
            
        } catch (error) {
            console.error('Error asking question:', error);
        }
    };


    const handleButtonClick = () => {
        if (isButtonEnabled) {
          navigate('/codemirror'); // Navigate to the next page after the interview is done
        }
    };

    return (
      <div className="gemini-page">
        <h1>Listen for questions about your resume!</h1>
        <p>Answer them out loud and Shamith will listen...</p>

        <div className="question-section">
          <p>Current Question: {currentQuestion || "Loading question..."}</p>
        </div>

        <button 
          className={`submit-button ${isButtonEnabled ? 'enabled' : 'disabled'}`} 
          onClick={handleButtonClick}
          disabled={!isButtonEnabled}
        >
          {isButtonEnabled ? 'Go to Technical' : 'Interview in process...'}
        </button>
      </div>
    );
};

export default ResumeQ;
