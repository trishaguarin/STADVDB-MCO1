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
  const [showTimeDropdown, setShowTimeDropdown] = useState(false);
  const [selectedCities, setSelectedCities] = useState([]);
  const [selectedGenders, setSelectedGenders] = useState([]);
  const [selectedTime, setSelectedTime] = useState([]);
  const cityDropdownRef = useRef(null);
  const genderDropdownRef = useRef(null);

  // Placeholder Data
  const cities = [
    'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
    'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'
  ];

  // Tab states and data
  const [activeTab, setActiveTab] = useState('orders');
  const [filters, setFilters] = useState({
    city: [],
    gender: [],
    dateRange: { start: '2025-01-01', end: '2025-01-31' }
  });

  const tabData = {
    orders: {
      title: 'Orders Analytics',
      stats: [
        { title: 'Average Order Value', value: '$124.75' },
        { title: 'Minimum Order Value', value: '$12.99' },
        { title: 'Maximum Order Value', value: '$1,249.99' }
      ],
      charts: [
        {
          type: 'line',
          title: 'Orders Over Time',
          description: 'Daily order volume for the selected period',
          dataKey: 'orders',
          data: Array.from({ length: 7 }, (_, i) => ({
            date: `2025-01-${String(i + 1).padStart(2, '0')}`,
            orders: Math.floor(Math.random() * 50) + 20
          }))
        },
        {
          type: 'bar',
          title: 'Order Value Distribution',
          description: 'Breakdown of orders by value range',
          dataKey: 'count',
          data: [
            { range: '$0-50', count: 320 },
            { range: '$51-100', count: 450 },
            { range: '$101-200', count: 280 },
            { range: '$201-500', count: 150 },
            { range: '$500+', count: 48 },
          ]
        }
      ]
    },
    users: {
      title: 'User Statistics',
      stats: [
        { title: 'Total Users', value: '2,450' },
        { title: 'New Users (30d)', value: '345' },
        { title: 'Active Users', value: '1,892' }
      ],
      charts: [
        {
          type: 'line',
          title: 'User Growth',
          description: 'New user signups over time',
          dataKey: 'users',
          data: Array.from({ length: 7 }, (_, i) => ({
            date: `2025-01-${String(i + 1).padStart(2, '0')}`,
            users: Math.floor(Math.random() * 30) + 5
          }))
        },
        {
          type: 'bar',
          title: 'User Activity',
          description: 'User engagement metrics',
          dataKey: 'count',
          data: [
            { activity: 'Page Views', count: 12450 },
            { activity: 'Sessions', count: 8450 },
            { activity: 'Purchases', count: 1248 },
            { activity: 'Returns', count: 75 }
          ]
        }
      ]
    },
    products: {
      title: 'Product Trends',
      stats: [
        { title: 'Total Products', value: '1,245' },
        { title: 'Top Selling', value: 'Product X' },
        { title: 'Low Stock', value: '42 items' }
      ],
      charts: [
        {
          type: 'line',
          title: 'Sales Trends',
          description: 'Product sales over time',
          dataKey: 'sales',
          data: Array.from({ length: 7 }, (_, i) => ({
            date: `2025-01-${String(i + 1).padStart(2, '0')}`,
            sales: Math.floor(Math.random() * 100) + 50
          }))
        },
        {
          type: 'bar',
          title: 'Top Products',
          description: 'Best selling products',
          dataKey: 'units',
          data: [
            { name: 'Product A', units: 450 },
            { name: 'Product B', units: 380 },
            { name: 'Product C', units: 290 },
            { name: 'Product D', units: 210 },
            { name: 'Product E', units: 180 }
          ]
        }
      ]
    },
    riders: {
      title: 'Rider Performance',
      stats: [
        { title: 'Total Riders', value: '42' },
        { title: 'Avg. Delivery Time', value: '28 min' },
        { title: 'On-time Rate', value: '96.5%' }
      ],
      charts: [
        {
          type: 'line',
          title: 'Delivery Performance',
          description: 'Average delivery time by day',
          dataKey: 'time',
          data: Array.from({ length: 7 }, (_, i) => ({
            date: `2025-01-${String(i + 1).padStart(2, '0')}`,
            time: Math.floor(Math.random() * 15) + 20
          }))
        },
        {
          type: 'bar',
          title: 'Rider Ratings',
          description: 'Average rider ratings',
          dataKey: 'rating',
          data: [
            { name: 'Rider 1', rating: 4.8 },
            { name: 'Rider 2', rating: 4.9 },
            { name: 'Rider 3', rating: 4.7 },
            { name: 'Rider 4', rating: 4.9 },
            { name: 'Rider 5', rating: 4.6 }
          ]
        }
      ]
    }
  };

  const currentTab = tabData[activeTab];
  const genders = ['Male', 'Female'];

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

  const toggleSelection = (item, selectedItems, setSelectedItems) => {
    setSelectedItems(prev => 
      prev.includes(item)
        ? prev.filter(i => i !== item)
        : [...prev, item]
    );
  };

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

            {/* Time Granularity Dropdown */}
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
                console.log('Selected Genders:', selectedGenders);
                console.log('Selected Cities:', selectedCities);
                console.log('Date Range:', { startDate, endDate });
              }}
            >
              Filter Results
            </button>
          </div>
        </aside>

        <div className="content-wrapper">
          {/* Tabs/buttons at the top */}
          <div className="tabs-container">
            <button
              className={`tab-button orders-tab ${activeTab === 'orders' ? 'active' : ''}`}
              onClick={() => setActiveTab('orders')}
            >
              Orders Analytics
            </button>

            <button
              className={`tab-button users-tab ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              User Statistics
            </button>

            <button
              className={`tab-button products-tab ${activeTab === 'products' ? 'active' : ''}`}
              onClick={() => setActiveTab('products')}
            >
              Product Trends
            </button>

            <button
              className={`tab-button riders-tab ${activeTab === 'riders' ? 'active' : ''}`}
              onClick={() => setActiveTab('riders')}
            >
              Rider Performance
            </button>
          </div>


          <main className={`main-content ${activeTab}-active`}>
            <div className="main-content-container">
              {/* Statistical Data */}
              <div className="statistical-data">
                <h2 className="section-title">Statistical Data</h2>
                {currentTab.stats.map((stat, index) => (
                  <div key={index} className="stat-card">
                    <h3>{stat.title}</h3>
                    <p>{stat.value}</p>
                  </div>
                ))}
              </div>

              <div className="chart-wrapper">
                <div className="chart-grid">
                  {currentTab.charts.map((chart, index) => (
                    <div key={index} className="chart-card">
                      <div className="chart-header">
                        <h3>{chart.title}</h3>
                        <p>{chart.description}</p>
                      </div>
                      <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                          {chart.type === 'line' ? (
                            <LineChart
                              data={chart.data}
                              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" vertical={false} />
                              <XAxis dataKey="date" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Line 
                                type="monotone" 
                                dataKey={chart.dataKey} 
                                stroke="#3b82f6" 
                                strokeWidth={2} 
                                dot={false} 
                              />
                            </LineChart>
                          ) : (
                            <BarChart
                              data={chart.data}
                              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" vertical={false} />
                              <XAxis dataKey={chart.dataKey === 'rating' ? 'name' : Object.keys(chart.data[0])[0]} />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Bar 
                                dataKey={chart.dataKey} 
                                fill="#3b82f6" 
                                radius={[4, 4, 0, 0]} 
                              />
                            </BarChart>
                          )}
                        </ResponsiveContainer>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </main>
        </div>

      </div>
    </div>
  );
}

export default OrdersAnalytics;