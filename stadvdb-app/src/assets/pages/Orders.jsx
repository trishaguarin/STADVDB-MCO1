// src/components/OrdersAnalytics.jsx
import React, { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Calendar, ChevronDown, Check } from 'lucide-react';
import '../../styles/Orders.css';

const OrdersAnalytics = () => {
  const API_BASE_URL = 'http://localhost:5000';

  // State Management
  const [activeTab, setActiveTab] = useState('orders');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-01-31');
  const [showStartCalendar, setShowStartCalendar] = useState(false);
  const [showEndCalendar, setShowEndCalendar] = useState(false);
  
  const [selectedTime, setSelectedTime] = useState('Month');
  const [selectedGenders, setSelectedGenders] = useState([]);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState([]);
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [selectedCities, setSelectedCities] = useState([]);
  
  const [showCityDropdown, setShowCityDropdown] = useState(false);
  const [showGenderDropdown, setShowGenderDropdown] = useState(false);
  const [showTimeDropdown, setShowTimeDropdown] = useState(false);
  const [showAgeGroupDropdown, setShowAgeGroupDropdown] = useState(false);
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  
  const [ordersData, setOrdersData] = useState({
    ordersOverTime: [],
    ordersByLocation: [],
    ordersByCategory: [],
    stats: { totalOrders: 0, uniqueCustomers: 0, totalItems: 0 }
  });
  
  const [countries, setCountries] = useState([]);
  const [availableCities, setAvailableCities] = useState([]);
  
  const timeOptions = ['Year', 'Quarter', 'Month', 'Day'];
  const ageGroups = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'];
  const genders = ['Male', 'Female'];
  
  const cityDropdownRef = useRef(null);
  const genderDropdownRef = useRef(null);
  const timeDropdownRef = useRef(null);
  const ageGroupDropdownRef = useRef(null);
  const countryDropdownRef = useRef(null);

  // Fetch Functions
  const fetchCountries = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/filters/countries`);
      const data = await response.json();
      if (data.success) setCountries(data.data);
    } catch (error) {
      console.error('Error fetching countries:', error);
    }
  };
  
  const fetchCities = async () => {
    try {
      const params = new URLSearchParams();
      
      // Get all selected country names
      const selectedCountryNames = selectedCountries.map(countryId => {
        const country = countries.find(c => c.id === countryId);
        return country ? country.name : null;
      }).filter(Boolean);
      
      // If we have selected countries, fetch cities for all of them
      if (selectedCountryNames.length > 0) {
        // Fetch cities for all selected countries
        const citiesPromises = selectedCountryNames.map(countryName => {
          return fetch(`${API_BASE_URL}/api/filters/cities?country=${encodeURIComponent(countryName)}`)
            .then(res => res.json())
            .then(data => data.success ? data.data : []);
        });
        
        const citiesResults = await Promise.all(citiesPromises);
        const allCities = citiesResults.flat();
        
        // Remove duplicates based on city and country
        const uniqueCities = Array.from(new Map(
          allCities.map(city => [`${city.city}_${city.country}`, city])
        ).values());
        
        setAvailableCities(uniqueCities);
      } else {
        // If no countries selected, fetch all cities
        const response = await fetch(`${API_BASE_URL}/api/filters/cities`);
        const data = await response.json();
        if (data.success) {
          setAvailableCities(data.data);
        }
      }
      
      // Clear selected cities if they're no longer in the filtered list
      if (selectedCities.length > 0) {
        const availableCityIds = new Set(availableCities.map(city => city.id));
        const validSelectedCities = selectedCities.filter(id => availableCityIds.has(id));
        
        if (validSelectedCities.length !== selectedCities.length) {
          setSelectedCities(validSelectedCities);
        }
      }
    } catch (error) {
      console.error('Error fetching cities:', error);
      setAvailableCities([]);
    } finally {
      if (selectedCountries.length === 0) {
        setSelectedCities([]);
      }
    }
  };

  const fetchOrdersData = async () => {
    console.log('🔄 Fetching data...');
    setLoading(true);
    setError(null);

    try {
      const timeMap = { 'Year': 'year', 'Quarter': 'quarter', 'Month': 'month', 'Day': 'day' };
      const baseParams = {
        start_date: startDate,
        end_date: endDate,
        category: timeMap[selectedTime] || 'month'
      };

      const timeUrl = `${API_BASE_URL}/api/orders/total-over-time?${new URLSearchParams(baseParams)}`;
      const timeResponse = await fetch(timeUrl);
      const timeData = await timeResponse.json();

      let locationData = [];
      if (selectedCities.length > 0) {
        const locationUrl = `${API_BASE_URL}/api/orders/by-location?${new URLSearchParams({
          start_date: startDate,
          end_date: endDate,
          type: 'city'
        })}`;
        const locationResponse = await fetch(locationUrl);
        const locationResponseData = await locationResponse.json();
        if (locationResponseData.success) locationData = locationResponseData.data;
      }

      const categoryUrl = `${API_BASE_URL}/api/orders/by-product-category?${new URLSearchParams({
        start_date: startDate,
        end_date: endDate
      })}`;
      const categoryResponse = await fetch(categoryUrl);
      const categoryData = await categoryResponse.json();

      setOrdersData({
        ordersOverTime: timeData.success ? timeData.data : [],
        ordersByLocation: locationData,
        ordersByCategory: categoryData.success ? categoryData.data : [],
        stats: {
          totalOrders: timeData.success ? timeData.data.reduce((sum, item) => sum + (item.total_orders || 0), 0) : 0,
          uniqueCustomers: timeData.success && timeData.data.length > 0 ? timeData.data[0].unique_customers || 0 : 0,
          totalItems: timeData.success ? timeData.data.reduce((sum, item) => sum + (item.total_items || 0), 0) : 0
        }
      });

      console.log('✅ Data loaded');
    } catch (err) {
      console.error('❌ Error:', err);
      setError('Failed to fetch data. Check if backend is running.');
    } finally {
      setLoading(false);
    }
  };

  // Effects
  useEffect(() => { fetchCountries(); }, []);
  useEffect(() => { fetchCities(); }, [selectedCountries, countries]);
  useEffect(() => { fetchOrdersData(); }, []);
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (cityDropdownRef.current && !cityDropdownRef.current.contains(event.target)) setShowCityDropdown(false);
      if (genderDropdownRef.current && !genderDropdownRef.current.contains(event.target)) setShowGenderDropdown(false);
      if (countryDropdownRef.current && !countryDropdownRef.current.contains(event.target)) setShowCountryDropdown(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Helper Functions
  const toggleSelection = (item, selectedItems, setSelectedItems) => {
    setSelectedItems(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item]);
  };

  const getSelectedText = (items, isCountry = false) => {
    if (items.length === 0) return 'Select...';
    if (isCountry) {
      if (items.length <= 2) {
        return items.map(id => countries.find(c => c.id === id)?.name || id).join(', ');
      }
      return `${items.length} countries selected`;
    }
    
    // For cities
    if (items.length <= 2) {
      return items
        .map(id => {
          const city = availableCities.find(c => c.id === id);
          return city ? `${city.city} (${city.country})` : id;
        })
        .join(', ');
    }
    return `${items.length} cities selected`;
  };

  const handleFilterClick = () => {
    console.log('🔍 Filter clicked');
    fetchOrdersData();
  };

  // Data Transformation
  const chartData = {
    ordersOverTime: ordersData.ordersOverTime.map(item => ({
      date: item.period,
      orders: item.total_orders || 0,
      customers: item.unique_customers || 0
    })),
    ordersByCategory: ordersData.ordersByCategory.map(item => ({
      category: item.category || 'Unknown',
      orders: item.total_orders || 0,
      quantity: item.total_quantity || 0
    })),
    ordersByLocation: ordersData.ordersByLocation.map(item => ({
      location: item.location || 'Unknown',
      orders: item.total_orders || 0
    }))
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
            
            {/* Start Date */}
            <div className="filter-item">
              <label className="filter-label">Start Date</label>
              <div className="date-picker">
                <input type="text" className="date-input" value={startDate} readOnly
                  onClick={() => setShowStartCalendar(!showStartCalendar)} placeholder="Select start date" />
                <Calendar className="calendar-icon" onClick={() => setShowStartCalendar(!showStartCalendar)} />
                {showStartCalendar && (
                  <div className="calendar-dropdown">
                    <input type="date" value={startDate} onChange={(e) => { setStartDate(e.target.value); setShowStartCalendar(false); }}
                      max={endDate} className="date-input" />
                  </div>
                )}
              </div>
            </div>

            {/* End Date */}
            <div className="filter-item">
              <label className="filter-label">End Date</label>
              <div className="date-picker">
                <input type="text" className="date-input" value={endDate} readOnly
                  onClick={() => setShowEndCalendar(!showEndCalendar)} placeholder="Select end date" />
                <Calendar className="calendar-icon" onClick={() => setShowEndCalendar(!showEndCalendar)} />
                {showEndCalendar && (
                  <div className="calendar-dropdown">
                    <input type="date" value={endDate} onChange={(e) => { setEndDate(e.target.value); setShowEndCalendar(false); }}
                      min={startDate} className="date-input" />
                  </div>
                )}
              </div>
            </div>

            {/* Time Granularity */}
            <div className="filter-item" ref={timeDropdownRef}>
              <label className="filter-label">Time Granularity</label>
              <div className="dropdown-container">
                <div className="dropdown-header" onClick={() => setShowTimeDropdown(!showTimeDropdown)}>
                  <span>{selectedTime || 'Select...'}</span>
                  <ChevronDown className={`dropdown-arrow ${showTimeDropdown ? 'rotate' : ''}`} />
                </div>
                {showTimeDropdown && (
                  <div className="dropdown-options">
                    {timeOptions.map(option => (
                      <div key={option} className={`dropdown-option ${selectedTime === option ? 'selected' : ''}`}
                        onClick={() => { setSelectedTime(option); setShowTimeDropdown(false); }}>
                        <span className="checkbox">{selectedTime === option && <Check size={14} />}</span>
                        {option}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Gender Filter */}
            {(activeTab === 'orders' || activeTab === 'users') && (
              <div className="filter-item" ref={genderDropdownRef}>
                <label className="filter-label">Gender</label>
                <div className="dropdown-container">
                  <div className="dropdown-header" onClick={() => setShowGenderDropdown(!showGenderDropdown)}>
                    <span className={selectedGenders.length === 0 ? 'placeholder' : ''}>{getSelectedText(selectedGenders)}</span>
                    <ChevronDown className={`dropdown-arrow ${showGenderDropdown ? 'rotate' : ''}`} />
                  </div>
                  {showGenderDropdown && (
                    <div className="dropdown-options">
                      {genders.map(gender => (
                        <div key={gender} className={`dropdown-option ${selectedGenders.includes(gender) ? 'selected' : ''}`}
                          onClick={() => toggleSelection(gender, selectedGenders, setSelectedGenders)}>
                          <span className="checkbox">{selectedGenders.includes(gender) && <Check size={14} />}</span>
                          {gender}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Age Group Filter */}
            {activeTab === 'users' && (
              <div className="filter-item" ref={ageGroupDropdownRef}>
                <label className="filter-label">Age Group</label>
                <div className="dropdown-container">
                  <div className="dropdown-header" onClick={() => setShowAgeGroupDropdown(!showAgeGroupDropdown)}>
                    <span className={selectedAgeGroups.length === 0 ? 'placeholder' : ''}>
                      {selectedAgeGroups.length === 0 ? 'Select...' : 
                       selectedAgeGroups.length <= 2 ? selectedAgeGroups.join(', ') : 
                       `${selectedAgeGroups.length} groups selected`}
                    </span>
                    <ChevronDown className={`dropdown-arrow ${showAgeGroupDropdown ? 'rotate' : ''}`} />
                  </div>
                  {showAgeGroupDropdown && (
                    <div className="dropdown-options">
                      {ageGroups.map(group => (
                        <div key={group} className={`dropdown-option ${selectedAgeGroups.includes(group) ? 'selected' : ''}`}
                          onClick={() => toggleSelection(group, selectedAgeGroups, setSelectedAgeGroups)}>
                          <span className="checkbox">{selectedAgeGroups.includes(group) && <Check size={14} />}</span>
                          {group}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Country Dropdown */}
            <div className="filter-item" ref={countryDropdownRef}>
              <label className="filter-label">Countries</label>
              <div className="dropdown-container">
                <div className="dropdown-header" onClick={() => setShowCountryDropdown(!showCountryDropdown)}>
                  <span className={selectedCountries.length === 0 ? 'placeholder' : ''}>{getSelectedText(selectedCountries, true)}</span>
                  <ChevronDown className={`dropdown-arrow ${showCountryDropdown ? 'rotate' : ''}`} />
                </div>
                {showCountryDropdown && (
                  <div className="dropdown-options">
                    {countries.map(country => (
                      <div key={country.id} className={`dropdown-option ${selectedCountries.includes(country.id) ? 'selected' : ''}`}
                        onClick={() => setSelectedCountries(prev => prev.includes(country.id) ? prev.filter(id => id !== country.id) : [...prev, country.id])}>
                        <span className="checkbox">{selectedCountries.includes(country.id) && <Check size={14} />}</span>
                        {country.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* City Dropdown */}
            <div className="filter-item" ref={cityDropdownRef}>
              <label className="filter-label">Cities</label>
              <div className={`dropdown-container ${selectedCountries.length === 0 ? 'disabled' : ''}`}>
                <div 
                  className="dropdown-header" 
                  onClick={() => { 
                    if (selectedCountries.length === 0) return; 
                    setShowCityDropdown(!showCityDropdown);
                    // Fetch cities when dropdown is opened if not already loaded
                    if (!showCityDropdown && availableCities.length === 0) {
                      fetchCities();
                    }
                  }}
                >
                  <span className={selectedCities.length === 0 ? 'placeholder' : ''}>
                    {selectedCountries.length === 0 
                      ? 'Select a country first...' 
                      : availableCities.length === 0 
                        ? 'No cities available' 
                        : getSelectedText(selectedCities)}
                  </span>
                  <ChevronDown className={`dropdown-arrow ${showCityDropdown ? 'rotate' : ''}`} />
                </div>
                {showCityDropdown && selectedCountries.length > 0 && (
                  <div className="dropdown-options">
                    {availableCities.length === 0 ? (
                      <div className="dropdown-option disabled">
                        {loading ? 'Loading cities...' : 'No cities available for selected country'}
                      </div>
                    ) : (
                      availableCities.map(city => (
                        <div 
                          key={city.id} 
                          className={`dropdown-option ${selectedCities.includes(city.id) ? 'selected' : ''}`}
                          onClick={() => toggleSelection(city.id, selectedCities, setSelectedCities)}
                          title={`${city.city}, ${city.country}`}
                        >
                          <span className="checkbox">
                            {selectedCities.includes(city.id) && <Check size={14} />}
                          </span>
                          {city.city} <span className="text-gray-500 text-sm">({city.country})</span>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Filter Button */}
            <button className="filter-button" onClick={handleFilterClick} disabled={loading}>
              {loading ? 'Loading...' : 'Filter Results'}
            </button>

            {error && <div style={{ color: 'red', marginTop: '10px', fontSize: '14px', padding: '10px', backgroundColor: '#fee', borderRadius: '4px' }}>{error}</div>}
          </div>
        </aside>

        <div className="content-wrapper">
          <div className="tabs-container">
            <button className={`tab-button orders-tab ${activeTab === 'orders' ? 'active' : ''}`} onClick={() => setActiveTab('orders')}>Orders Analytics</button>
            <button className={`tab-button users-tab ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>User Statistics</button>
            <button className={`tab-button products-tab ${activeTab === 'products' ? 'active' : ''}`} onClick={() => setActiveTab('products')}>Product Trends</button>
            <button className={`tab-button riders-tab ${activeTab === 'riders' ? 'active' : ''}`} onClick={() => setActiveTab('riders')}>Rider Performance</button>
          </div>

          <main className={`main-content ${activeTab}-active`}>
            <div className="main-content-container">
              {loading && <div style={{ textAlign: 'center', padding: '40px' }}><div style={{ fontSize: '18px', marginBottom: '10px' }}>⏳ Loading data...</div></div>}
              
              {!loading && activeTab === 'orders' && (
                <div className="chart-wrapper">
                  <div className="chart-grid">
                    <div className="chart-card">
                      <div className="chart-header">
                        <h3>Orders Over Time</h3>
                        <p>Showing {chartData.ordersOverTime.length} data points</p>
                      </div>
                      <div className="chart-container">
                        {chartData.ordersOverTime.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData.ordersOverTime} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} />
                              <XAxis dataKey="date" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Line type="monotone" dataKey="orders" stroke="#3b82f6" strokeWidth={2} name="Total Orders" />
                              <Line type="monotone" dataKey="customers" stroke="#10b981" strokeWidth={2} name="Unique Customers" />
                            </LineChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="no-data">No data available for the selected filters</div>
                        )}
                      </div>
                    </div>

                    <div className="chart-card">
                      <div className="chart-header">
                        <h3>Orders by Product Category</h3>
                        <p>Top {chartData.ordersByCategory.length} categories</p>
                      </div>
                      <div className="chart-container">
                        {chartData.ordersByCategory.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData.ordersByCategory} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="category" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Bar dataKey="orders" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Total Orders" />
                              <Bar dataKey="quantity" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Total Quantity" />
                            </BarChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="no-data">No category data available</div>
                        )}
                      </div>
                    </div>

                    {chartData.ordersByLocation.length > 0 && (
                      <div className="chart-card">
                        <div className="chart-header">
                          <h3>Orders by Location</h3>
                          <p>{chartData.ordersByLocation.length} locations</p>
                        </div>
                        <div className="chart-container">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData.ordersByLocation} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="location" />
                              <YAxis />
                              <Tooltip />
                              <Legend />
                              <Bar dataKey="orders" fill="#10b981" radius={[4, 4, 0, 0]} name="Total Orders" />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Users Tab */}
              {!loading && activeTab === 'users' && (
                <div className="chart-wrapper">
                  <div className="chart-grid">
                    <div className="chart-card">
                      <div className="chart-header">
                        <h3>User Registrations Over Time</h3>
                        <p>Showing user growth</p>
                      </div>
                      <div className="chart-container">
                        <div className="coming-soon">
                          <div className="coming-soon-content">
                            <h3>User Statistics</h3>
                            <p>User analytics and statistics will be displayed here</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="chart-card">
                      <div className="chart-header">
                        <h3>User Demographics</h3>
                        <p>Age and gender distribution</p>
                      </div>
                      <div className="chart-container">
                        <div className="coming-soon">
                          <div className="coming-soon-content">
                            <h3>Demographics</h3>
                            <p>User demographic charts will be displayed here</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Products Tab */}
              {!loading && activeTab === 'products' && (
                <div className="chart-wrapper">
                  <div className="chart-grid">
                    <div className="chart-card">
                      <div className="chart-header">
                        <h3>Product Performance</h3>
                        <p>Top performing products</p>
                      </div>
                      <div className="chart-container">
                        <div className="coming-soon">
                          <div className="coming-soon-content">
                            <h3>Product Trends</h3>
                            <p>Product performance metrics will be displayed here</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="chart-card">
                      <div className="chart-header">
                        <h3>Inventory Levels</h3>
                        <p>Current stock status</p>
                      </div>
                      <div className="chart-container">
                        <div className="coming-soon">
                          <div className="coming-soon-content">
                            <h3>Inventory</h3>
                            <p>Inventory management charts will be displayed here</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Riders Tab */}
              {!loading && activeTab === 'riders' && (
                <div className="chart-wrapper">
                  <div className="chart-grid">
                    <div className="chart-card">
                      <div className="chart-header">
                        <h3>Rider Performance</h3>
                        <p>Delivery metrics and ratings</p>
                      </div>
                      <div className="chart-container">
                        <div className="coming-soon">
                          <div className="coming-soon-content">
                            <h3>Rider Analytics</h3>
                            <p>Rider performance metrics will be displayed here</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="chart-card">
                      <div className="chart-header">
                        <h3>Delivery Times</h3>
                        <p>Average delivery duration</p>
                      </div>
                      <div className="chart-container">
                        <div className="coming-soon">
                          <div className="coming-soon-content">
                            <h3>Delivery Analytics</h3>
                            <p>Delivery performance metrics will be displayed here</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {!loading && activeTab !== 'orders' && (
                <div style={{ textAlign: 'center', padding: '60px' }}>
                  <h2>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Tab</h2>
                  <p style={{ color: '#666', marginTop: '10px' }}>Ready for your content</p>
                </div>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default OrdersAnalytics;