import React from 'react';
import MoistureSensor from './MoistureSensor';
import GraphsField from './GraphsField';

interface BodyProps {
  deviceId: string;
}

const Body: React.FC<BodyProps> = ({ deviceId }) => {
  console.log('Body component rendered');
  return (
    <div className="body-container">
      <MoistureSensor deviceId={deviceId} />
      <GraphsField deviceId={deviceId} />
    </div>
  );
};

export default Body;