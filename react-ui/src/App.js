
import './picker.css'
import React from 'react';
import Theme from './Theme';
import axios from 'axios';

const App = () => {
  const [themes, setThemes] = React.useState([]); // You'd fetch this data

  React.useEffect(() => {
    axios.get('/layers/top_level_themes/')
      .then(response => {
        setThemes(response.data.top_level_themes);
      })
      .catch(error => console.error('Error fetching themes:', error));
  }, []);

  return (
    <div className="datacontainer">
      <div className="datasidebar" id="sidebar">
        {themes.map((theme) => (
          <Theme key={theme.id} theme={theme} level={0} />
        ))}
      </div>
    </div>
  );
};

export default App;
