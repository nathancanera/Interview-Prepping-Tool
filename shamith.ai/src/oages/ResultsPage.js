import React, { useEffect, useState } from 'react';
import RatingStars from '../components/RatingStars.js';
import './resultsPage.css';

const ResultsPage = () => {
  const [scores, setScores] = useState(null);  // State to store the fetched scores
  const [loading, setLoading] = useState(true); // State to manage loading
  const [error, setError] = useState(null); // State to manage errors

  // Fetch the scores when the component mounts
  useEffect(() => {
    const fetchScores = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/evaluate', {  // Call to your /evaluate endpoint
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            // Send relevant data that your /evaluate endpoint expects (e.g., code, transcript, etc.)
            code: "def solution(nums): return sum([x for x in nums if x > 0 and x % 2 == 0])", // Example code
            transcript: "Sample interview transcript here", // Replace with actual transcript if needed
            questions: ["Sample question 1", "Sample question 2"] // Replace with actual stored questions
          }),
        });

        const data = await response.json();

        if (data.success) {
          setScores(data.scores);  // Set the fetched scores to state
        } else {
          setError('Failed to fetch scores');
        }
      } catch (err) {
        setError('An error occurred while fetching scores');
      } finally {
        setLoading(false);  // Set loading to false once request is completed
      }
    };

    fetchScores();
  }, []);

  if (loading) {
    return <p>Loading...</p>;
  }

  if (error) {
    return <p>Error: {error}</p>;
  }

  return (
    <div className="results-page">
      <h1>Interview Results</h1>

      {scores && (
        <>
          <div className="metric">
            <h2>Code Correctness</h2>
            <RatingStars score={scores.codeCorrectness || 5} />
          </div>

          <div className="metric">
            <h2>Communication</h2>
            <RatingStars score={scores.communication || 5} />
          </div>

          <div className="metric">
            <h2>Answers to Resume Questions</h2>
            <RatingStars score={scores.resumeQuestions || 5} />
          </div>

          <div className="metric">
            <h2>Answers to Technical Questions</h2>
            <RatingStars score={scores.technicalQuestions || 5} />
          </div>
        </>
      )}
    </div>
  );
};

export default ResultsPage;
