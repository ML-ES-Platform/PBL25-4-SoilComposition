import React from 'react';
import MoistureSensor from './MoistureSensor.tsx';
import GraphsField from './GraphsField.tsx';

const Body: React.FC = () => {
  console.log('Body component rendered');
  return (
    <div className="body-container">
      <MoistureSensor />
      <GraphsField />
    </div>
  );
};

export default Body;