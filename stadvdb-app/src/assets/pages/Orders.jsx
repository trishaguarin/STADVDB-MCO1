import React, { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Calendar, ChevronDown, X, Check } from 'lucide-react';
import '../../styles/Orders.css';

const OrdersAnalytics = () => {
  // Date states
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-01-31');
  const [showStartCalendar, setShowStartCalendar] = useState(false);
  const [showEndCalendar, setShowEndCalendar] = useState(false);
  
  // Dropdown states
  const [showCityDropdown, setShowCityDropdown] = useState(false);
  const [showGenderDropdown, setShowGenderDropdown] = useState(false);
  const [selectedCities, setSelectedCities] = useState([]);
  const [selectedGenders, setSelectedGenders] = useState([]);
  const cityDropdownRef = useRef(null);
  const genderDropdownRef = useRef(null);

  // Placeholder Data
  const cities = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
    'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'
  ];

  const genders = ['Male', 'Female'];

  const data = [
    // Sample data
    { name: 'Jan', sales: 4000},
    { name: 'Feb', sales: 3000 },
    { name: 'Mar', sales: 2000 },
    { name: 'Apr', sales: 2780 },
    { name: 'May', sales: 1890 },
    { name: 'Jun', sales: 2390 },
  ];

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (cityDropdownRef.current && !cityDropdownRef.current.contains(event.target)) {
        setShowCityDropdown(false);
      }
      if (genderDropdownRef.current && !genderDropdownRef.current.contains(event.target)) {
        setShowGenderDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Toggle selections
  const toggleSelection = (item, selectedItems, setSelectedItems) => {
    setSelectedItems(prev => 
      prev.includes(item)
        ? prev.filter(i => i !== item)
        : [...prev, item]
    );
  };

  // Format selected items for display
  const getSelectedText = (items) => {
    if (items.length === 0) return 'Select...';
    if (items.length <= 2) return items.join(', ');
    return `${items.length} selected`;
  };



  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="header-title">OLAP Analytical Dashboard</h1>
      </header>

      <div className="dashboard-content">
        <aside className="sidebar">
          <h2 className="sidebar-title">Data Navigation</h2>

          <div className="filter-group">
            {/* Start Date Picker */}
            <div className="filter-item">
              <label className="filter-label">Start Date</label>
              <div className="date-picker">
                <input
                  type="text"
                  className="date-input"
                  value={startDate}
                  readOnly
                  onClick={() => setShowStartCalendar(!showStartCalendar)}
                  placeholder="Select start date"
                />
                <Calendar className="calendar-icon" onClick={() => setShowStartCalendar(!showStartCalendar)} />
                {showStartCalendar && (
                  <div className="calendar-dropdown">
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => {
                        setStartDate(e.target.value);
                        setShowStartCalendar(false);
                      }}
                      max={endDate}
                      className="date-input"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* End Date Picker */}
            <div className="filter-item">
              <label className="filter-label">End Date</label>
              <div className="date-picker">
                <input
                  type="text"
                  className="date-input"
                  value={endDate}
                  readOnly
                  onClick={() => setShowEndCalendar(!showEndCalendar)}
                  placeholder="Select end date"
                />
                <Calendar className="calendar-icon" onClick={() => setShowEndCalendar(!showEndCalendar)} />
                {showEndCalendar && (
                  <div className="calendar-dropdown">
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => {
                        setEndDate(e.target.value);
                        setShowEndCalendar(false);
                      }}
                      min={startDate}
                      className="date-input"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Gender Dropdown */}
            <div className="filter-item" ref={genderDropdownRef}>
              <label className="filter-label">Gender</label>
              <div className="dropdown-container">
                <div 
                  className="dropdown-header"
                  onClick={() => setShowGenderDropdown(!showGenderDropdown)}
                >
                  <span className={selectedGenders.length === 0 ? 'placeholder' : ''}>
                    {getSelectedText(selectedGenders)}
                  </span>
                  <ChevronDown className={`dropdown-arrow ${showGenderDropdown ? 'rotate' : ''}`} />
                </div>
                
                {showGenderDropdown && (
                  <div className="dropdown-options">
                    {genders.map(gender => (
                      <div 
                        key={gender} 
                        className={`dropdown-option ${selectedGenders.includes(gender) ? 'selected' : ''}`}
                        onClick={() => toggleSelection(gender, selectedGenders, setSelectedGenders)}
                      >
                        <span className="checkbox">
                          {selectedGenders.includes(gender) && <Check size={14} />}
                        </span>
                        {gender}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Cities Multi-Select Dropdown */}
            <div className="filter-item" ref={cityDropdownRef}>
              <label className="filter-label">City</label>
              <div className="dropdown-container">
                <div 
                  className="dropdown-header"
                  onClick={() => setShowCityDropdown(!showCityDropdown)}
                >
                  <span className={selectedCities.length === 0 ? 'placeholder' : ''}>
                    {getSelectedText(selectedCities)}
                  </span>
                  <ChevronDown className={`dropdown-arrow ${showCityDropdown ? 'rotate' : ''}`} />
                </div>
                
                {showCityDropdown && (
                  <div className="dropdown-options">
                    {cities.map(city => (
                      <div 
                        key={city} 
                        className={`dropdown-option ${selectedCities.includes(city) ? 'selected' : ''}`}
                        onClick={() => toggleSelection(city, selectedCities, setSelectedCities)}
                      >
                        <span className="checkbox">
                          {selectedCities.includes(city) && <Check size={14} />}
                        </span>
                        {city}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {/* Filter Button */}
            <button 
              className="filter-button"
              onClick={() => {
                // Filter logic here
                console.log('Selected Genders:', selectedGenders);
                console.log('Selected Cities:', selectedCities);
                console.log('Date Range:', { startDate, endDate });
              }}
            >
              Filter Results
            </button>
          </div>
        </aside>

        <main className="main-content">
          <div className="main-content-container">
            {/* Charts and analytics area */}
            <div className="chart-wrapper">
              <div className="chart-grid">
                <div className="chart-card">
                  {/* Chart components */}
                </div>
              </div>
            </div>

            {/* Statistical Data */}
            <div className="statistical-data">
              <h2>Statistical Data</h2>
            </div>

          </div>
        </main>

      </div>
    </div>
  );
}

export default OrdersAnalytics;