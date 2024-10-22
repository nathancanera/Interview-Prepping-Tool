import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]); // State to hold questions
  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];

    // Validate the file type
    if (file && file.type === 'application/pdf') {
      const formData = new FormData();
      formData.append('resume', file);
      fetch('http://127.0.0.1:5000/upload-resume', {
        method: 'POST',
        body: formData,
      })
      .then(response => response.json())
      .then(data => {
        // Handle the response from the server
        if (data.success) {
            setQuestions(data.questions)
            alert(`Resume uploaded and processed: ${file.name}`);
        } else {
            alert('Error processing resume.');
        }
      })
      .catch(error => {
        console.error('Error uploading resume:', error);
        alert('Failed to upload resume.');
      });
    } else {
      alert('Please upload a PDF file.');
    }
}, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: 'application/pdf',
    maxFiles: 1,
  });

  const handleShamithClick = () => {
    navigate('/ResumeQ', { state: { questions } });
  };

  return (
    <div className="landing-page">
      <div >
        <h1 className='LandingHeader'>Shamith.ai</h1>
      </div>

      <div {...getRootProps({ className: 'dropzone' })}>
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the PDF here...</p>
        ) : (
          <p>Drag & drop your resume here, or click to select a PDF</p>
        )}
      </div>
      <button className='ShamithButton' onClick={handleShamithClick}>Continue</button>
    </div>
  );
};

export default LandingPage;
