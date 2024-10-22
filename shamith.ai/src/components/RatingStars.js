import React from 'react';
import '../components/RatingStars.css';

const RatingStars = ({ score }) => {
  const maxStars = 5;

  return (
    <div className="rating-stars">
      {[...Array(maxStars)].map((star, index) => {
        return (
          <span key={index} className={index < score ? "star filled" : "star"}>
            ★
          </span>
        );
      })}
    </div>
  );
};

export default RatingStars;
