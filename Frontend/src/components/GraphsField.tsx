import React from 'react';
import GraphLast12H from './GraphLast12H.tsx';
import GraphLast24H from './GraphLast24H.tsx';
import GraphLast7D from './GraphLast7D.tsx';
import GraphNext12H from './GraphNext12H.tsx';

const GraphsField: React.FC = () => {
  return (
    <div className="graphs-field">
      <h2>Moisture Graphs</h2>
      <div className="graphs-flex">
        <GraphLast12H />
        <GraphLast24H />
        <GraphLast7D />
        <GraphNext12H />
      </div>
    </div>
  );
};

export default GraphsField;