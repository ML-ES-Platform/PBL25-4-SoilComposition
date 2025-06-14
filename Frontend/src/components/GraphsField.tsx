import React from 'react';
import GraphLast12H from './GraphLast12H';
import GraphLast24H from './GraphLast24H';
import GraphLast7D from './GraphLast7D';
import GraphNext12H from './GraphNext12H';

interface GraphsFieldProps {
  deviceId: string;
}

const GraphsField: React.FC<GraphsFieldProps> = ({ deviceId }) => {
  return (
    <div className="graphs-field">
      <GraphLast12H deviceId={deviceId} />
      <GraphLast24H deviceId={deviceId} />
      <GraphLast7D deviceId={deviceId} />
      <GraphNext12H deviceId={deviceId} />
    </div>
  );
};

export default GraphsField;